"""
metrics.py
----------
Strict metric validation and calculation based on task types.
"""

from __future__ import annotations

from typing import Dict, List, Literal
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, mean_squared_error, mean_absolute_error

TaskType = Literal["binary_occurrence", "multiclass_horizon", "regression_size"]


def evaluate_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    task_type: TaskType,
) -> Dict[str, float]:
    """
    Evaluates metrics based on task_type.
    Rejects invalid labels/metric combinations.
    """
    # Enforce label validation
    if task_type == "binary_occurrence":
        # Check that labels are binary (only 0 and 1)
        unique_vals = np.unique(y_true)
        for val in unique_vals:
            if not np.isclose(val, 0.0) and not np.isclose(val, 1.0):
                raise ValueError(
                    f"Invalid labels for binary_occurrence: found continuous/non-binary value {val}. "
                    f"All values must be strictly 0 or 1."
                )
        
        # Binary classification metrics
        y_pred = (y_score >= 0.5).astype(np.int32)
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        try:
            auc = float(roc_auc_score(y_true, y_score))
        except ValueError:
            auc = float("nan") # single class present in split
        
        return {"f1": f1, "auc": auc}

    elif task_type == "multiclass_horizon":
        # Check that labels are integers
        if not np.all(np.equal(np.mod(y_true, 1), 0)):
            raise ValueError("Labels for multiclass_horizon must be integers.")
        
        # Dummy multiclass classification
        y_pred = np.argmax(y_score, axis=-1) if y_score.ndim > 1 else (y_score >= 0.5).astype(np.int32)
        f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        return {"f1_macro": f1}

    elif task_type == "regression_size":
        # Regression metrics only
        mse = float(mean_squared_error(y_true, y_score))
        mae = float(mean_absolute_error(y_true, y_score))
        return {"mse": mse, "mae": mae}
    
    else:
        raise ValueError(f"Unknown task_type: {task_type}")
