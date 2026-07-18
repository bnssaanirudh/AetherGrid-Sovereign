import json
import logging
from typing import List, Dict, Set, Any
from .event_dataset import EventSample

logger = logging.getLogger(__name__)

class SplitAuditReport:
    def __init__(self):
        self.passed: bool = True
        self.issues: List[str] = []
        self.stats: Dict[str, Any] = {}

    def log_issue(self, msg: str):
        self.passed = False
        self.issues.append(msg)
        logger.warning(msg)

    def to_json(self) -> str:
        return json.dumps({
            "passed": self.passed,
            "issues": self.issues,
            "stats": self.stats
        }, indent=2)


class LeakageSafeSplitter:
    @staticmethod
    def temporal_holdout(samples: List[EventSample], cutoff_date: str) -> tuple[List[EventSample], List[EventSample]]:
        train, test = [], []
        for s in samples:
            if s.observation_window_start < cutoff_date:
                train.append(s)
            else:
                test.append(s)
        return train, test

    @staticmethod
    def group_holdout(samples: List[EventSample], test_groups: Set[str], group_fn) -> tuple[List[EventSample], List[EventSample]]:
        train, test = [], []
        for s in samples:
            if group_fn(s) in test_groups:
                test.append(s)
            else:
                train.append(s)
        return train, test
        
    @staticmethod
    def district_holdout(samples: List[EventSample], test_districts: Set[str], district_fn) -> tuple[List[EventSample], List[EventSample]]:
        return LeakageSafeSplitter.group_holdout(samples, test_districts, district_fn)

    @staticmethod
    def audit_splits(train: List[EventSample], test: List[EventSample]) -> SplitAuditReport:
        report = SplitAuditReport()
        
        # 1. Duplicated snapshots check
        train_snaps = {s.snapshot_id for s in train}
        test_snaps = {s.snapshot_id for s in test}
        overlap_snaps = train_snaps.intersection(test_snaps)
        if overlap_snaps:
            report.log_issue(f"Leakage: {len(overlap_snaps)} duplicated snapshots between train and test.")
            
        # 2. Overlapping outcome windows check
        # Simplified: Check if any test observation window overlaps with any train outcome window
        # (Assuming sorted by time for efficiency in a real impl, here O(N*M) for demonstration)
        for tr in train:
            for te in test:
                # If test happens during train outcome
                if tr.outcome_window_start <= te.observation_window_start <= tr.outcome_window_end:
                    if tr.snapshot_id == te.snapshot_id or tr.trigger_nodes == te.trigger_nodes:
                         report.log_issue(f"Leakage: Overlapping windows between train {tr.snapshot_id} and test {te.snapshot_id}")
                         
        # 3. Post-event features check
        # A true check would require schema validation, here we just flag if it's not strictly 'pre'
        for s in test:
            if "post_event" in str(s.sensor_features):
                report.log_issue(f"Leakage: Post-event features found in test sample {s.snapshot_id}")

        report.stats = {
            "train_size": len(train),
            "test_size": len(test),
            "train_snaps": len(train_snaps),
            "test_snaps": len(test_snaps)
        }
        
        return report
