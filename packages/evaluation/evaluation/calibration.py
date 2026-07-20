import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.metrics import brier_score_loss
from typing import Dict, Any, Tuple

class TemperatureScaler(nn.Module):
    """
    Post-hoc Temperature Scaling on validation data to calibrate logits.
    """
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature

    def fit(self, val_logits: torch.Tensor, val_labels: torch.Tensor, lr: float = 0.01, max_iter: int = 100):
        """
        Fits the temperature to the validation set using NLLLoss.
        """
        nll_criterion = nn.BCEWithLogitsLoss() if val_logits.dim() == 1 or val_logits.shape[-1] == 1 else nn.CrossEntropyLoss()
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def eval():
            optimizer.zero_grad()
            loss = nll_criterion(self(val_logits), val_labels)
            loss.backward()
            return loss
            
        optimizer.step(eval)
        return self

class CalibrationMetrics:
    @staticmethod
    def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
        """Computes ECE using equal-width bins."""
        bins = np.linspace(0., 1., n_bins + 1)
        binids = np.digitize(y_prob, bins) - 1
        
        ece = 0.0
        for i in range(n_bins):
            mask = binids == i
            if np.any(mask):
                prob_pred = np.mean(y_prob[mask])
                prob_true = np.mean(y_true[mask])
                ece += (np.sum(mask) / len(y_prob)) * np.abs(prob_pred - prob_true)
        return float(ece)

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
        ece = CalibrationMetrics.expected_calibration_error(y_true, y_prob)
        brier = float(brier_score_loss(y_true, y_prob))
        return {
            "expected_calibration_error": ece,
            "brier_score": brier
        }
