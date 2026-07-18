"""
checkpoints.py
--------------
Safe and versioned checkpoint saving/loading.
"""

from __future__ import annotations

import logging
import platform
import torch
from typing import Dict, Any, Optional
from aethergrid_core import ModelArtifactManifest

logger = logging.getLogger(__name__)


def save_checkpoint(
    path: str,
    model: torch.nn.Module,
    config_hash: str,
    data_manifest_hash: str,
    source_commit: str,
    task_schema: Dict[str, Any],
    optimizer: Optional[torch.optim.Optimizer] = None,
    epoch: int = 0,
) -> None:
    """Saves a model checkpoint with versioned metadata manifest."""
    manifest = ModelArtifactManifest(
        model_class=model.__class__.__name__,
        config_hash=config_hash,
        data_manifest_hash=data_manifest_hash,
        source_commit=source_commit,
        python_version=platform.python_version(),
        torch_version=torch.__version__,
        cuda_version=torch.version.cuda if torch.cuda.is_available() else None,
        task_schema=task_schema,
        id=f"checkpoint_epoch_{epoch}",
    )

    state = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
        "manifest": manifest.model_dump(),
    }
    torch.save(state, path)
    logger.info("Saved versioned checkpoint to %s", path)


def load_checkpoint(
    path: str,
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
) -> Dict[str, Any]:
    """
    Loads a checkpoint and verifies the model class compatibility.
    Raises ValueError on mismatches.
    """
    state = torch.load(path, map_location="cpu", weights_only=False)
    manifest_dict = state.get("manifest", {})
    
    if not manifest_dict:
        raise ValueError("Checkpoint is missing versioned metadata manifest.")

    manifest = ModelArtifactManifest(**manifest_dict)
    current_class = model.__class__.__name__

    if manifest.model_class != current_class:
        raise ValueError(
            f"Model class mismatch! Checkpoint expects '{manifest.model_class}' but loaded model is '{current_class}'."
        )

    model.load_state_dict(state["model_state_dict"])
    if optimizer and state.get("optimizer_state_dict"):
        optimizer.load_state_dict(state["optimizer_state_dict"])

    logger.info("Successfully verified and loaded checkpoint from %s (Epoch %d)", path, state["epoch"])
    return state
