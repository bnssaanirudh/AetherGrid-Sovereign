import numpy as np
import json
from typing import List, Dict, Any
from theory.bounds import BoundResult

class BoundValidationProtocol:
    """
    Validates cascade amplification bounds over held-out events.
    Computes coverage, tightness, and stratifies by various factors.
    """
    def __init__(self, target_coverage: float = 0.95):
        self.target_coverage = target_coverage

    def validate(self, bound_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        bound_results: list of dicts containing:
        - bound_result: BoundResult object
        - graph_size: int
        - dropout_level: float
        - cascade_type: str
        - district: str
        """
        total = len(bound_results)
        if total == 0:
            return {"error": "No bound results to validate"}

        covered = 0
        tightness_values = []
        failure_cases = []
        stratified_coverage = {
            "graph_size": {"small": [0,0], "medium": [0,0], "large": [0,0]},
            "dropout_level": {"low": [0,0], "high": [0,0]},
            "cascade_type": {},
            "district": {}
        }

        for item in bound_results:
            br: BoundResult = item['bound_result']
            is_covered = br.coverage_indicator
            if is_covered is None:
                continue
                
            if is_covered:
                covered += 1
            else:
                failure_cases.append({
                    "district": item.get('district', 'unknown'),
                    "computed_bound": br.computed_bound,
                    "observed": br.observed_outcome
                })
                
            if br.tightness_ratio is not None:
                tightness_values.append(br.tightness_ratio)
                
            # Stratification: Graph Size
            size = item.get('graph_size', 0)
            if size < 50:
                s_key = "small"
            elif size < 200:
                s_key = "medium"
            else:
                s_key = "large"
            stratified_coverage["graph_size"][s_key][1] += 1
            if is_covered: stratified_coverage["graph_size"][s_key][0] += 1
                
            # Stratification: Dropout Level
            dropout = item.get('dropout_level', 0.0)
            d_key = "low" if dropout < 0.2 else "high"
            stratified_coverage["dropout_level"][d_key][1] += 1
            if is_covered: stratified_coverage["dropout_level"][d_key][0] += 1
                
            # Cascade Type
            ctype = item.get('cascade_type', 'default')
            if ctype not in stratified_coverage["cascade_type"]:
                stratified_coverage["cascade_type"][ctype] = [0, 0]
            stratified_coverage["cascade_type"][ctype][1] += 1
            if is_covered: stratified_coverage["cascade_type"][ctype][0] += 1
                
            # District
            district = item.get('district', 'unknown')
            if district not in stratified_coverage["district"]:
                stratified_coverage["district"][district] = [0, 0]
            stratified_coverage["district"][district][1] += 1
            if is_covered: stratified_coverage["district"][district][0] += 1

        overall_coverage = covered / total
        mean_tightness = float(np.mean(tightness_values)) if tightness_values else float('inf')
        
        # Format stratification to percentages
        for cat in stratified_coverage:
            for k in stratified_coverage[cat]:
                c, t = stratified_coverage[cat][k]
                stratified_coverage[cat][k] = float(c / t) if t > 0 else 0.0

        # Confidence Interval (Normal approximation for binomial)
        z = 1.96 # 95% CI
        ci_margin = z * np.sqrt((overall_coverage * (1 - overall_coverage)) / total)
        
        target_met = overall_coverage >= self.target_coverage

        return {
            "total_events": total,
            "overall_coverage": float(overall_coverage),
            "coverage_ci_95": [float(overall_coverage - ci_margin), float(overall_coverage + ci_margin)],
            "mean_tightness": mean_tightness,
            "target_coverage_met": bool(target_met),
            "stratified_coverage": stratified_coverage,
            "num_failure_cases": len(failure_cases)
        }
