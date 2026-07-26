"""
registry.py
-----------
Lightweight local model/run registry utility that logs run credentials and statistics.
"""

from __future__ import annotations

import os
import sys
import json
import time
import platform
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

class LocalExperimentRegistry:
    """
    Manages a local file-based run registry. Stores runs as exportable/canonical JSON manifests.
    """
    def __init__(self, registry_dir: str = "runs") -> None:
        self.registry_dir = registry_dir
        os.makedirs(registry_dir, exist_ok=True)

    def _get_git_commit(self) -> str:
        try:
            out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            return out.decode("utf-8").strip()
        except Exception:
            return "unknown-commit"

    def _get_hardware_info(self) -> Dict[str, Any]:
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version.split()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
        try:
            import torch
            info["torch_version"] = torch.__version__
            info["cuda_available"] = torch.cuda.is_available()
            if info["cuda_available"]:
                info["cuda_device_name"] = torch.cuda.get_device_name(0)
        except Exception:
            pass
        return info

    def create_run(
        self,
        model_name: str,
        hyperparameters: Dict[str, Any],
        seed: int,
        fuzzy_family: str = "IFS",
        phase_variant: str = "none",
        dropout_rate: float = 0.1,
        missingness_conditions: Optional[Dict[str, Any]] = None,
        snapshot_hash: str = "unknown_hash",
        training_budget: str = "standard",
    ) -> Dict[str, Any]:
        run_id = f"run_{int(time.time() * 1000)}_{seed}_{hashlib.md5(model_name.encode()).hexdigest()[:6]}"
        manifest = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "code_commit": self._get_git_commit(),
            "environment_hardware": self._get_hardware_info(),
            "model_variant": model_name,
            "phase_variant": phase_variant,
            "fuzzy_family": fuzzy_family,
            "hyperparameters": {**hyperparameters, "seed": seed},
            "seed": seed,
            "dropout_rate": dropout_rate,
            "missingness_conditions": missingness_conditions or {},
            "snapshot_hash": snapshot_hash,
            "training_budget": training_budget,
            "calibration_artifact": None,
            "status": "running",
            "retries": 0,
            "failure_reason": None,
            "metrics": {},
            "latency_ms": 0.0,
            "peak_memory_mb": 0.0,
        }
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest: Dict[str, Any]) -> None:
        run_id = manifest["run_id"]
        filepath = os.path.join(self.registry_dir, f"{run_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def update_run(
        self,
        run_id: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        failure_reason: Optional[str] = None,
        calibration_artifact: Optional[str] = None,
        latency_ms: float = 0.0,
        peak_memory_mb: float = 0.0,
    ) -> Dict[str, Any]:
        filepath = os.path.join(self.registry_dir, f"{run_id}.json")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Run {run_id} not found.")
            
        with open(filepath, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest["status"] = status
        manifest["metrics"] = metrics or {}
        manifest["failure_reason"] = failure_reason
        manifest["calibration_artifact"] = calibration_artifact
        manifest["latency_ms"] = latency_ms
        manifest["peak_memory_mb"] = peak_memory_mb
        manifest["timestamp_updated"] = datetime.utcnow().isoformat() + "Z"

        self.save_manifest(manifest)
        return manifest

    def export_all_runs(self, output_path: str = "artifacts/experiment_registry_export.json") -> None:
        runs = []
        for filename in os.listdir(self.registry_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.registry_dir, filename), "r", encoding="utf-8") as f:
                    runs.append(json.load(f))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(runs, f, indent=2)
