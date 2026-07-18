import numpy as np
from typing import Tuple, List, Dict, Union

class SplitConformalPredictor:
    """
    Implements distribution-free prediction intervals/sets using Split Conformal Prediction.
    Requires a held-out calibration set.
    """
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        self.q_hat_regression: float = 0.0
        self.q_hat_classification: float = 0.0

    def calibrate_regression(self, y_cal: np.ndarray, y_pred_cal: np.ndarray) -> None:
        """
        Calibrates for size/radius prediction intervals.
        Computes nonconformity scores (absolute error).
        """
        n = len(y_cal)
        scores = np.abs(y_cal - y_pred_cal)
        
        # Finite-sample correction
        val = np.ceil((n + 1) * (1 - self.alpha)) / n
        val = min(val, 1.0)
        self.q_hat_regression = float(np.quantile(scores, val, method='higher'))

    def predict_interval(self, y_pred_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (lower_bound, upper_bound)
        """
        lower = y_pred_test - self.q_hat_regression
        # Size/radius are non-negative
        lower = np.maximum(0.0, lower)
        upper = y_pred_test + self.q_hat_regression
        return lower, upper

    def calibrate_classification(self, y_cal: np.ndarray, y_prob_cal: np.ndarray) -> None:
        """
        Calibrates for occurrence prediction sets.
        Computes nonconformity scores (1 - predicted probability of true class).
        Assumes y_prob_cal is [n_samples, n_classes] or [n_samples] for binary prob of class 1.
        """
        n = len(y_cal)
        if y_prob_cal.ndim == 1:
            # Binary
            prob_true_class = np.where(y_cal == 1, y_prob_cal, 1 - y_prob_cal)
        else:
            # Multiclass
            prob_true_class = y_prob_cal[np.arange(n), y_cal.astype(int)]
            
        scores = 1.0 - prob_true_class
        
        val = np.ceil((n + 1) * (1 - self.alpha)) / n
        val = min(val, 1.0)
        self.q_hat_classification = float(np.quantile(scores, val, method='higher'))

    def predict_set_binary(self, y_prob_test: np.ndarray) -> List[List[int]]:
        """
        Returns prediction sets for binary classification.
        e.g. [[0], [1], [0, 1]]
        """
        sets = []
        for p in y_prob_test:
            s = []
            if (1.0 - (1.0 - p)) <= self.q_hat_classification:
                s.append(0)
            if (1.0 - p) <= self.q_hat_classification:
                s.append(1)
            # Guarantee non-empty (fallback to argmax if set is empty due to strict numerical edge cases)
            if not s:
                s.append(1 if p >= 0.5 else 0)
            sets.append(s)
        return sets
        
    def export_summary(self) -> Dict[str, float]:
        return {
            "alpha": self.alpha,
            "q_hat_regression": self.q_hat_regression,
            "q_hat_classification": self.q_hat_classification
        }
