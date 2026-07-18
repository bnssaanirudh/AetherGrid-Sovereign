import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Set, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

@dataclass
class SamplingCoverage:
    eligible_nodes: int
    included_nodes: int
    eligible_edges: int
    included_edges: int
    dropped_relation_types: Dict[str, int]
    boundary_cuts: int
    trigger_connectivity: float

@dataclass
class EventSample:
    # Core identifiers
    snapshot_id: str
    observation_window_start: str
    observation_window_end: str
    trigger_nodes: List[str]
    
    # Pre-trigger features
    pre_trigger_node_features: Dict[str, Any]
    pre_trigger_edge_features: Dict[str, Any]
    sensor_features: Dict[str, Any]
    hazard_features: Dict[str, Any]
    uncertainty_features: Dict[str, Any]
    
    # Graph structure
    sampled_ego_network: Dict[str, Any]  # Could be edge index and node list
    sampling_coverage: SamplingCoverage
    
    # Outcomes
    outcome_window_start: str
    outcome_window_end: str
    occurrence_label: int  # 0 or 1
    affected_nodes: Set[str]
    cascade_size: float
    graph_radius: float
    physical_radius: float
    failure_time_horizon: str  # E.g., 'short', 'medium', 'long'
    per_node_event_times: Dict[str, str]
    
    # Interventions and provenance
    intervention_counterfactuals: Dict[str, Any]
    label_provenance: str

class DatasetSerializer:
    @staticmethod
    def to_json(sample: EventSample) -> str:
        d = asdict(sample)
        d['affected_nodes'] = list(d['affected_nodes'])
        return json.dumps(d)

    @staticmethod
    def from_json(data: str) -> EventSample:
        d = json.loads(data)
        d['affected_nodes'] = set(d['affected_nodes'])
        d['sampling_coverage'] = SamplingCoverage(**d['sampling_coverage'])
        return EventSample(**d)

    @staticmethod
    def save_pickle(sample: EventSample, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(sample, f)

    @staticmethod
    def load_pickle(path: Path) -> EventSample:
        with open(path, 'rb') as f:
            return pickle.load(f)

class EventDatasetIndex:
    def __init__(self, index_file: Path):
        self.index_file = index_file
        self.samples: Dict[str, str] = {} # trigger_id_hash -> file_path
        if self.index_file.exists():
            self.load()
            
    def add(self, sample_id: str, path: str):
        self.samples[sample_id] = path
        
    def load(self):
        with open(self.index_file, 'r') as f:
            self.samples = json.load(f)
            
    def save(self):
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(self.samples, f, indent=2)
