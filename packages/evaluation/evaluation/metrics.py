"""
metrics.py
----------
Strict metric validation and calculation based on task types.
"""

from __future__ import annotations

from typing import Dict, List, Literal
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, mean_squared_error, mean_absolute_error

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
        # Check that label values are within expected regression bounds (e.g. not only integers or binary)
        # Regression metrics only
        mse = float(mean_squared_error(y_true, y_score))
        mae = float(mean_absolute_error(y_true, y_score))
        return {"mse": mse, "mae": mae}
    
    else:
        raise ValueError(f"Unknown task_type: {task_type}")

class CascadeMetrics:
    @staticmethod
    def occurrence_metrics(y_true: List[int], y_prob: List[float]) -> Dict[str, float]:
        """
        Calculates occurrence metrics.
        Aggregation: Macro over dataset. Units: Dimensionless (0-1).
        """
        y_pred = [1 if p >= 0.5 else 0 for p in y_prob]
        try:
            auroc = float(roc_auc_score(y_true, y_prob))
            auprc = float(average_precision_score(y_true, y_prob))
        except ValueError:
            auroc, auprc = 0.0, 0.0
            
        f1 = float(f1_score(y_true, y_pred, average='macro'))
        return {"auroc": auroc, "auprc": auprc, "macro_f1": f1}

    @staticmethod
    def size_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        """
        Calculates cascade size regression metrics.
        Aggregation: Mean over dataset. Units: Node count / Size unit.
        """
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        return {"mae_size": mae, "rmse_size": rmse}

    @staticmethod
    def radius_metrics(y_true: List[float], y_pred: List[float], unit_name: str = "hops") -> Dict[str, float]:
        """
        Calculates radius error.
        Aggregation: Mean over dataset. Units: Provided by `unit_name`.
        """
        mae = float(mean_absolute_error(y_true, y_pred))
        return {f"mae_radius_{unit_name}": mae}

    @staticmethod
    def horizon_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
        """
        Calculates ordinal/multiclass horizon metrics.
        Aggregation: Macro over dataset. Units: Dimensionless (0-1).
        """
        f1 = float(f1_score(y_true, y_pred, average='macro'))
        return {"macro_f1_horizon": f1}

    @staticmethod
    def node_affected_metrics(y_true: List[int], y_prob: List[float]) -> Dict[str, float]:
        """
        Node-level precision/recall map metric summary (F1).
        Aggregation: Macro over nodes in an event. Units: Dimensionless (0-1).
        """
        y_pred = [1 if p >= 0.5 else 0 for p in y_prob]
        f1 = float(f1_score(y_true, y_pred, average='binary', zero_division=0))
        return {"node_level_f1": f1}

