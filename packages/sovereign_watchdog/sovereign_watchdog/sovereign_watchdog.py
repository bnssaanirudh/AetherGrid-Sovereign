"""
sovereign_watchdog.py
---------------------
Pydantic-based structural integrity validator for the Urban Digital Twin graph.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Optional, Literal

import torch
from pydantic import BaseModel, Field, field_validator
from torch_geometric.data import HeteroData

from core.schema import NODE_TYPES, EDGE_TYPES, FEATURE_DIMS

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    INFO    = "INFO"
    WARNING = "WARNING"
    ERROR   = "ERROR"
    FATAL   = "FATAL"


class CheckResult(BaseModel):
    check_name: str
    passed: bool
    severity: Severity = Severity.INFO
    message: str = ""
    details: Optional[Dict] = None

    @field_validator("severity", mode="before")
    @classmethod
    def coerce_severity(cls, v):
        if isinstance(v, str):
            return Severity(v.upper())
        return v


class ValidationReport(BaseModel):
    epoch: int = 0
    checks: List[CheckResult] = Field(default_factory=list)
    overall_passed: bool = True
    fatal_messages: List[str] = Field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)
        if not result.passed:
            if result.severity in (Severity.ERROR, Severity.FATAL):
                self.overall_passed = False
                self.fatal_messages.append(result.message)

    def summary(self) -> str:
        n_pass = sum(1 for c in self.checks if c.passed)
        n_fail = len(self.checks) - n_pass
        return (
            f"ValidationReport(epoch={self.epoch}, "
            f"passed={n_pass}/{len(self.checks)}, "
            f"failed={n_fail}, "
            f"overall={'✓ OK' if self.overall_passed else '✗ FAILED'})"
        )


class SovereignWatchdog:
    """
    Validates HeteroData graph integrity before each training epoch.
    """

    def __init__(
        self,
        strict: bool = True,
        profile: Literal["research", "production"] = "research",
    ) -> None:
        self.strict = strict
        self.profile = profile

    def validate(self, data: HeteroData, epoch: int = 0) -> ValidationReport:
        report = ValidationReport(epoch=epoch)

        self._check_profile_fallback(data, report)
        self._check_node_features(data, report)
        self._check_edge_indices(data, report)
        self._check_edge_attr_shapes(data, report)
        self._check_ifs_constraints(data, report)
        self._check_edge_attr_ranges(data, report)
        self._check_nan_inf(data, report)
        self._check_connectivity(data, report)

        logger.info("[Watchdog] %s", report.summary())

        if self.strict and not report.overall_passed:
            raise WatchdogError(
                f"Graph integrity FAILED at epoch {epoch}:\n"
                + "\n".join(f"  ✗ {m}" for m in report.fatal_messages)
            )
        if not self.strict and not report.overall_passed:
            logger.warning("[Watchdog] Non-strict mode: %s", report.summary())

        return report

    def _check_profile_fallback(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        if self.profile == "production":
            is_synthetic_graph = getattr(data, "is_synthetic", False)
            allow_demo = getattr(data, "allow_demo", False)
            if is_synthetic_graph and not allow_demo:
                report.add(CheckResult(
                    check_name="profile/synthetic_fallback",
                    passed=False,
                    severity=Severity.FATAL,
                    message="Production profile active but synthetic fallback detected without explicit allow_demo flag.",
                ))

    def _check_node_features(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        for ntype in NODE_TYPES:
            expected_dim = FEATURE_DIMS[ntype]
            if not hasattr(data[ntype], "x"):
                report.add(CheckResult(
                    check_name=f"node_features/{ntype}",
                    passed=False,
                    severity=Severity.FATAL,
                    message=f"Node type '{ntype}' is missing feature tensor 'x'.",
                ))
                continue

            actual_dim = data[ntype].x.size(1)
            passed = (actual_dim == expected_dim)
            report.add(CheckResult(
                check_name=f"node_features/{ntype}",
                passed=passed,
                severity=Severity.FATAL if not passed else Severity.INFO,
                message=(
                    f"'{ntype}' feature dim={actual_dim} (expected {expected_dim})"
                    if not passed else f"'{ntype}' features OK (dim={actual_dim})"
                ),
            ))

    def _check_edge_indices(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        counts = {nt: data[nt].num_nodes for nt in NODE_TYPES}
        for src_type, rel, dst_type in EDGE_TYPES:
            store = data[src_type, rel, dst_type]
            if "edge_index" not in store:
                # Missing edge types are warnings, not fatal errors
                report.add(CheckResult(
                    check_name=f"edge_indices/{src_type}__{rel}__{dst_type}",
                    passed=True,
                    severity=Severity.WARNING,
                    message=f"{src_type}__{rel}__{dst_type}: no edge_index present",
                ))
                continue
            ei = store.edge_index
            if ei.size(1) == 0:
                report.add(CheckResult(
                    check_name=f"edge_indices/{src_type}__{rel}__{dst_type}",
                    passed=True,
                    severity=Severity.WARNING,
                    message=f"{src_type}__{rel}__{dst_type}: empty edge_index",
                ))
                continue
            n_src, n_dst = counts[src_type], counts[dst_type]
            src_ok = (ei[0].max().item() < n_src) if ei.numel() > 0 else True
            dst_ok = (ei[1].max().item() < n_dst) if ei.numel() > 0 else True
            passed = src_ok and dst_ok
            key = f"edge_indices/{src_type}__{rel}__{dst_type}"
            report.add(CheckResult(
                check_name=key,
                passed=passed,
                severity=Severity.FATAL if not passed else Severity.INFO,
                message=(
                    f"{key}: index out of bounds (src_max={ei[0].max().item()}/{n_src}, dst_max={ei[1].max().item()}/{n_dst})"
                    if not passed else f"{key}: indices OK"
                ),
            ))

    def _check_edge_attr_shapes(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        for src_type, rel, dst_type in EDGE_TYPES:
            store = data[src_type, rel, dst_type]
            key = f"edge_attr/{src_type}__{rel}__{dst_type}"
            if not hasattr(store, "edge_index"):
                continue
            if not hasattr(store, "edge_attr"):
                report.add(CheckResult(
                    check_name=key,
                    passed=False,
                    severity=Severity.ERROR,
                    message=f"{key}: missing edge_attr",
                ))
                continue
            ei = store.edge_index
            ea = store.edge_attr
            passed = ea.size(0) == ei.size(1) and ea.size(1) >= 4
            report.add(CheckResult(
                check_name=key,
                passed=passed,
                severity=Severity.ERROR if not passed else Severity.INFO,
                message=(
                    f"{key}: shape mismatch (edge_attr={tuple(ea.shape)} edge_index={tuple(ei.shape)})"
                    if not passed else f"{key}: shapes OK"
                ),
            ))

    def _check_ifs_constraints(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        for src_type, rel, dst_type in EDGE_TYPES:
            store = data[src_type, rel, dst_type]
            if not hasattr(store, "edge_attr"):
                continue
            ea = store.edge_attr
            mu, nu = ea[:, 0], ea[:, 1]
            sum_mn = mu + nu
            violations = (sum_mn > 1.0 + 1e-5).sum().item()
            pi_violations = ((1.0 - sum_mn) < -1e-5).sum().item()
            passed = (violations == 0) and (pi_violations == 0)
            key = f"ifs/{src_type}__{rel}__{dst_type}"
            report.add(CheckResult(
                check_name=key,
                passed=passed,
                severity=Severity.ERROR if not passed else Severity.INFO,
                message=(
                    f"{key}: {violations} edges violate mu+nu<=1 ({pi_violations} with pi<0)"
                    if not passed else f"{key}: IFS constraints satisfied"
                ),
                details={"violations": violations, "pi_violations": pi_violations},
            ))

    def _check_edge_attr_ranges(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        for src_type, rel, dst_type in EDGE_TYPES:
            store = data[src_type, rel, dst_type]
            if not hasattr(store, "edge_attr"):
                continue
            ea = store.edge_attr
            mu, nu, tau = ea[:, 0], ea[:, 1], ea[:, 3]
            in_range = (
                (mu >= 0).all() and (mu <= 1).all()
                and (nu >= 0).all() and (nu <= 1).all()
                and (tau >= 0).all() and (tau <= 1).all()
            )
            key = f"edge_attr_range/{src_type}__{rel}__{dst_type}"
            report.add(CheckResult(
                check_name=key,
                passed=in_range,
                severity=Severity.ERROR if not in_range else Severity.INFO,
                message=(
                    f"{key}: values must be in [0, 1]"
                    if not in_range else f"{key}: ranges OK"
                ),
            ))

    def _check_nan_inf(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        for ntype in NODE_TYPES:
            if hasattr(data[ntype], "x"):
                x = data[ntype].x
                has_nan = torch.isnan(x).any().item()
                has_inf = torch.isinf(x).any().item()
                passed = not (has_nan or has_inf)
                report.add(CheckResult(
                    check_name=f"nan_inf/node/{ntype}",
                    passed=passed,
                    severity=Severity.FATAL if not passed else Severity.INFO,
                    message=(
                        f"'{ntype}' features contain {'NaN' if has_nan else ''}{'Inf' if has_inf else ''}"
                        if not passed else f"'{ntype}' features clean"
                    ),
                ))

    def _check_connectivity(
        self, data: HeteroData, report: ValidationReport
    ) -> None:
        total_edges = 0
        for src_type, rel, dst_type in EDGE_TYPES:
            store = data[src_type, rel, dst_type]
            if hasattr(store, "edge_index"):
                n = store.edge_index.size(1)
                total_edges += n
        passed = total_edges > 0
        report.add(CheckResult(
            check_name="connectivity/total_edges",
            passed=passed,
            severity=Severity.FATAL if not passed else Severity.INFO,
            message=(
                "Graph has zero edges — cannot train."
                if not passed else f"Graph connectivity OK: {total_edges} total edges"
            ),
        ))


class WatchdogError(RuntimeError):
    """Raised when SovereignWatchdog detects a fatal graph integrity failure."""
