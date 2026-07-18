"""
splits.py
---------
Leakage-safe temporal splitting for graph snapshots.
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Any
from datetime import datetime


def temporal_split(
    snapshots: List[Dict[str, Any]],
    train_ratio: float = 0.7,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Sorts snapshots by timestamp and splits them to prevent temporal leakage.
    Each snapshot must contain a 'timestamp' key (datetime object or ISO string).
    """
    if not snapshots:
        return [], []

    def get_time(s: Dict[str, Any]) -> datetime:
        ts = s.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.min

    sorted_snapshots = sorted(snapshots, key=get_time)
    n_train = max(1, int(len(sorted_snapshots) * train_ratio))
    
    train_split = sorted_snapshots[:n_train]
    val_split = sorted_snapshots[n_train:]
    
    # Check for leakage
    detect_leakage(train_split, val_split)
    
    return train_split, val_split


def detect_leakage(
    train_snapshots: List[Dict[str, Any]],
    val_snapshots: List[Dict[str, Any]],
) -> None:
    """
    Detects temporal order leakage. Raises ValueError if validation
    snapshots occur before or concurrent with training snapshots.
    """
    if not train_snapshots or not val_snapshots:
        return

    def get_time(s: Dict[str, Any]) -> datetime:
        ts = s.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.min

    max_train_time = max(get_time(s) for s in train_snapshots)
    min_val_time = min(get_time(s) for s in val_snapshots)

    if min_val_time <= max_train_time:
        raise ValueError(
            f"Temporal leakage detected! Min validation snapshot timestamp ({min_val_time}) "
            f"is earlier than or equal to Max training snapshot timestamp ({max_train_time})."
        )
