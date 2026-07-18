"""
train.py
--------
Main training script for AetherGrid-Sovereign.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import logging
import time
import json
import random
import platform
import hashlib
from typing import Dict, Optional, Tuple, Literal

import torch
import torch.nn.functional as F
import yaml
import numpy as np

# Monorepo imports
from graph_builder import GraphConfig, UrbanGraphConstructor
from models import AetherHGT
from sovereign_watchdog import SovereignWatchdog, WatchdogError
from training import save_checkpoint, load_checkpoint
from evaluation import evaluate_metrics, TaskType

logger = logging.getLogger("AetherGrid")


def load_config(path: str = "configs/default_config.yaml") -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_seed(seed: int, deterministic: bool = False) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False


def make_masks(
    data, val_ratio: float, seed: int, node_types: list
) -> Dict[str, Tuple[torch.Tensor, torch.Tensor]]:
    rng = np.random.default_rng(seed)
    masks = {}
    for nt in node_types:
        n = data[nt].num_nodes
        if n < 2:
            train_mask = torch.ones(n, dtype=torch.bool)
            val_mask = torch.ones(n, dtype=torch.bool)
            masks[nt] = (train_mask, val_mask)
            continue
        idx = rng.permutation(n)
        n_val = max(1, int(n * val_ratio))
        n_val = min(n - 1, n_val)
        val_idx = torch.tensor(idx[:n_val], dtype=torch.long)
        train_idx = torch.tensor(idx[n_val:], dtype=torch.long)
        train_mask = torch.zeros(n, dtype=torch.bool)
        val_mask = torch.zeros(n, dtype=torch.bool)
        train_mask[train_idx] = True
        val_mask[val_idx] = True
        masks[nt] = (train_mask, val_mask)
    return masks


def make_labels(data, device: torch.device, seed: int, node_types: list, binary: bool = False) -> Dict[str, torch.Tensor]:
    """Create synthetic labels (either continuous or binary)."""
    gen = torch.Generator(device=device).manual_seed(seed)
    labels = {}
    for nt in node_types:
        n = data[nt].num_nodes
        if binary:
            labels[nt] = (torch.rand(n, generator=gen, device=device) > 0.5).to(torch.float32)
        else:
            base = 0.3 if nt != "power" else 0.5
            noise = torch.rand(n, generator=gen, device=device) * 0.2
            labels[nt] = (torch.full((n,), base, device=device) + noise).clamp(0, 1)
    return labels


def load_labels(cfg: Dict, data, device: torch.device, node_types: list, binary: bool = False) -> Dict[str, torch.Tensor]:
    labels_cfg = cfg["training"].get("labels", {})
    mode = labels_cfg.get("mode", "synthetic")
    if mode == "synthetic":
        return make_labels(data, device, cfg["training"]["seed"], node_types, binary)

    path = labels_cfg.get("path")
    if not path:
        raise ValueError("labels.path is required when labels.mode='file'")

    if path.endswith(".pt"):
        raw = torch.load(path, map_location=device)
    elif path.endswith(".npz"):
        raw = dict(np.load(path))
    else:
        raise ValueError("Unsupported label format. Use .pt or .npz")

    labels = {}
    for nt in node_types:
        if nt not in raw:
            raise KeyError(f"Missing labels for node type: {nt}")
        labels[nt] = torch.tensor(raw[nt], dtype=torch.float32, device=device)
    return labels


def compute_loss(
    preds: Dict[str, torch.Tensor],
    labels: Dict[str, torch.Tensor],
    masks: Dict[str, Tuple[torch.Tensor, torch.Tensor]],
    split: str,
    node_types: list,
    task_type: TaskType,
) -> torch.Tensor:
    loss = 0.0
    for nt in node_types:
        if nt not in preds:
            continue
        train_mask, val_mask = masks[nt]
        mask = train_mask if split == "train" else val_mask
        p = preds[nt].squeeze(-1)[mask]
        y = labels[nt][mask]
        if task_type == "regression_size":
            loss = loss + F.mse_loss(p, y)
        else:
            loss = loss + F.binary_cross_entropy(p, y)
    return loss


def train(config_path: str = "configs/default_config.yaml", seed_override: Optional[int] = None) -> None:
    cfg = load_config(config_path)
    if seed_override is not None:
        cfg["training"]["seed"] = seed_override

    # Determine profile: research or production
    profile = cfg.get("profile", "research")
    task_type: TaskType = cfg["training"].get("task_type", "regression_size")

    # Set up logging level and target
    log_level = cfg["logging"]["level"]
    log_file = cfg["logging"].get("log_file")
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=log_level, filename=log_file, format="%(asctime)s [%(levelname)s] %(message)s")

    set_seed(cfg["training"]["seed"], deterministic=cfg["training"].get("deterministic", False))
    device = torch.device(cfg["training"]["device"] if torch.cuda.is_available() else "cpu")

    # Check for synthetic fallback warning/error in production profile
    if profile == "production" and cfg["graph"].get("use_toy_data", False):
        raise RuntimeError("Production profile does not allow synthetic/toy data fallback.")

    # Build Graph
    logger.info("Building urban heterogeneous graph...")
    graph_cfg = GraphConfig(**cfg["graph"])
    constructor = UrbanGraphConstructor(config=graph_cfg)
    data = constructor.build()
    
    # Label synthetic flag on graph data
    data.is_synthetic = cfg["graph"].get("use_toy_data", True) or cfg["graph"].get("num_power", 50) > 0
    data.allow_demo = cfg["graph"].get("allow_demo", False)

    data = data.to(device)

    # Resolve HGT node types
    node_types = list(data.node_types)
    edge_types = list(data.edge_types)

    # Set up model config
    arch_params = cfg["model"]
    # Pass explicit monorepo fields
    arch_params["node_types"] = node_types
    arch_params["edge_types"] = edge_types
    arch_params["feature_dims"] = {nt: data[nt].x.size(1) for nt in node_types}
    arch_params["fuzzy_family"] = cfg.get("fuzzy_family", "IFS")

    model = AetherHGT(**arch_params).to(device)
    logger.info("Model: %d trainable parameters", model.count_parameters())

    lr = cfg["training"]["learning_rate"]
    optimizer  = torch.optim.Adam(
        model.parameters(), lr=lr,
        weight_decay=cfg["training"]["weight_decay"]
    )
    scheduler  = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg["training"]["epochs"]
    )

    # Watchdog initialization
    watchdog = SovereignWatchdog(strict=cfg["watchdog"]["strict"], profile=profile)
    watch_every = cfg["watchdog"]["run_every_n_epochs"]

    # Labels loading
    binary_labels = (task_type == "binary_occurrence")
    labels = load_labels(cfg, data, device, node_types, binary=binary_labels)
    masks = make_masks(data, cfg["training"]["val_ratio"], cfg["training"]["seed"], node_types)

    best_loss = float("inf")
    patience_counter = 0
    out_dir = Path(cfg["training"].get("output_dir", "runs"))
    out_dir.mkdir(exist_ok=True)
    history = []

    # Calculate config and data hashes for versioned checkpoints
    config_str = yaml.safe_dump(cfg)
    config_hash = hashlib.sha256(config_str.encode("utf-8")).hexdigest()
    data_manifest_hash = hashlib.sha256(str(data).encode("utf-8")).hexdigest()

    logger.info("Starting training for %d epochs...", cfg["training"]["epochs"])
    for epoch in range(1, cfg["training"]["epochs"] + 1):
        t0 = time.time()

        # Watchdog validation
        if epoch % watch_every == 0:
            try:
                report = watchdog.validate(data, epoch=epoch)
                if not report.overall_passed:
                    logger.error("[Watchdog] Epoch %d: %s", epoch, report.summary())
            except WatchdogError as e:
                logger.critical("Training halted by watchdog: %s", e)
                raise e

        # 1. Train Step
        model.train()
        optimizer.zero_grad()
        train_preds, _ = model(data, return_attention=False)
        train_loss = compute_loss(train_preds, labels, masks, split="train", node_types=node_types, task_type=task_type)
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), cfg["training"]["grad_clip"]
        )
        optimizer.step()
        scheduler.step()

        # 2. Validation Step (separate forward pass, eval mode, no grad)
        model.eval()
        with torch.no_grad():
            val_preds, _ = model(data, return_attention=False)
            val_loss = compute_loss(val_preds, labels, masks, split="val", node_types=node_types, task_type=task_type)

        # Compute metrics based on task_type
        train_y_true = np.concatenate([labels[nt][masks[nt][0]].cpu().numpy() for nt in node_types])
        train_y_score = np.concatenate([train_preds[nt].squeeze(-1)[masks[nt][0]].detach().cpu().numpy() for nt in node_types])
        train_metrics = evaluate_metrics(train_y_true, train_y_score, task_type)

        val_y_true = np.concatenate([labels[nt][masks[nt][1]].cpu().numpy() for nt in node_types])
        val_y_score = np.concatenate([val_preds[nt].squeeze(-1)[masks[nt][1]].detach().cpu().numpy() for nt in node_types])
        val_metrics = evaluate_metrics(val_y_true, val_y_score, task_type)

        elapsed = time.time() - t0
        metric_str = " | ".join(f"{k}={v:.4f}" for k, v in val_metrics.items())
        logger.info(
            "Epoch %3d/%d | train=%.4f | val=%.4f | %s | lr=%.5f | t=%.2fs",
            epoch, cfg["training"]["epochs"],
            train_loss.item(),
            val_loss.item(),
            metric_str,
            scheduler.get_last_lr()[0],
            elapsed,
        )

        history.append({
            "epoch": epoch,
            "train_loss": float(train_loss.item()),
            "val_loss": float(val_loss.item()),
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
        })

        if val_loss.item() < best_loss:
            best_loss = val_loss.item()
            patience_counter = 0
            # Save safe, versioned checkpoint
            save_checkpoint(
                path=str(out_dir / "best_model.pt"),
                model=model,
                config_hash=config_hash,
                data_manifest_hash=data_manifest_hash,
                source_commit="init_commit",
                task_schema={"task_type": task_type, "node_types": node_types},
                optimizer=optimizer,
                epoch=epoch,
            )
        else:
            patience_counter += 1
            if patience_counter >= cfg["training"]["patience"]:
                logger.info("Early stopping at epoch %d (patience=%d).",
                            epoch, cfg["training"]["patience"])
                break

    metadata = {
        "best_val_loss": float(best_loss),
        "arch": arch_params,
        "config": cfg,
        "history": history,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "device": str(device),
        },
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Training complete. Best val loss: %.4f", best_loss)


def main() -> None:
    parser = argparse.ArgumentParser(description="AetherGrid-Sovereign Trainer")
    parser.add_argument("--config", default="configs/default_config.yaml")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    train(args.config, seed_override=args.seed)


if __name__ == "__main__":
    main()
