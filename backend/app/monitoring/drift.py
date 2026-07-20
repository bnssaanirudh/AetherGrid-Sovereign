import numpy as np
from typing import Dict, Any, List
from ..config import settings

def ks_2samp_numpy(data1: np.ndarray, data2: np.ndarray) -> float:
    """Computes the Kolmogorov-Smirnov statistic for two samples using NumPy."""
    d1, d2 = np.sort(data1), np.sort(data2)
    n1, n2 = len(d1), len(d2)
    if n1 == 0 or n2 == 0:
        return 0.0
    data_all = np.concatenate([d1, d2])
    cdf1 = np.searchsorted(d1, data_all, side='right') / n1
    cdf2 = np.searchsorted(d2, data_all, side='right') / n2
    return float(np.max(np.abs(cdf1 - cdf2)))


class DriftMonitor:
    """Measured drift monitoring framework matching Work Package G specifications."""
    def __init__(self) -> None:
        self.min_samples = settings.DRIFT_MIN_SAMPLE_SIZE
        self.threshold = settings.DRIFT_THRESHOLD_KS

    def check_feature_drift(self, baseline: List[float], current: List[float]) -> Dict[str, Any]:
        """Calculates KS-statistic feature distribution drift."""
        if len(baseline) < self.min_samples or len(current) < self.min_samples:
            return {
                "drift_detected": False,
                "reason_code": "INSUFFICIENT_SAMPLES",
                "message": f"Sample size below minimum requirement of {self.min_samples}."
            }
            
        ks_stat = ks_2samp_numpy(np.array(baseline), np.array(current))
        drift_detected = ks_stat > self.threshold
        
        return {
            "drift_detected": drift_detected,
            "metric_name": "kolmogorov_smirnov",
            "observed_value": ks_stat,
            "threshold": self.threshold,
            "message": "Drift detected. Model review workflow triggered." if drift_detected else "No significant drift."
        }

    def check_topology_drift(self, baseline_density: float, current_density: float) -> Dict[str, Any]:
        """Simple topological density delta checker."""
        density_diff = abs(baseline_density - current_density)
        drift_detected = density_diff > 0.1 # generous tolerance
        
        return {
            "drift_detected": drift_detected,
            "metric_name": "density_delta",
            "observed_value": density_diff,
            "threshold": 0.1,
            "message": "Topological drift detected." if drift_detected else "Topology within normal bounds."
        }
