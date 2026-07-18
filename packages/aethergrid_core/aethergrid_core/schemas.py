"""
Domain schemas for AetherGrid-Sovereign.
These are framework-agnostic Pydantic models representing nodes, edges, states, triggers, and evaluations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Tuple, Union, Any
from pydantic import BaseModel, Field, model_validator


# Node and Relation Types
NodeType = Literal["road_segment", "power_node", "weather_station", "poi_social_node", "control_response_node"]
RelationType = Literal["connects", "powers", "observes", "adjacent_to", "impacts", "intervention", "control"]

# Legacy Aliases
LEGACY_NODE_MAPPING = {
    "road": "road_segment",
    "power": "power_node",
    "hospital": "poi_social_node",
    "citizen": "poi_social_node",
}

def resolve_node_type(ntype: str) -> NodeType:
    """Resolve legacy node type to new domain node type."""
    resolved = LEGACY_NODE_MAPPING.get(ntype, ntype)
    if resolved not in ["road_segment", "power_node", "weather_station", "poi_social_node", "control_response_node"]:
        raise ValueError(f"Unknown or invalid node type: {ntype}")
    return resolved


class BaseRecord(BaseModel):
    schema_version: str = "1.0.0"
    id: str = Field(..., description="Stable unique identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the record creation/observation")
    source: str = Field("unknown", description="Source or provenance of the data")
    is_synthetic: bool = Field(default=False, description="Flag indicating if data is synthetic/simulated")
    validation_status: str = Field("unverified", description="E.g., verified, quarantined, draft")


class NodeRecord(BaseRecord):
    node_type: NodeType
    crs: Optional[str] = Field(None, description="Coordinate Reference System metadata (e.g. EPSG:4326)")
    coordinates: Optional[Tuple[float, float]] = Field(None, description="Longitude/Latitude or spatial coords")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary attributes matching node type")


class EdgeRecord(BaseRecord):
    src_id: str
    dst_id: str
    relation: RelationType
    attributes: Dict[str, Any] = Field(default_factory=dict)


class FuzzyState(BaseModel):
    membership: float = Field(..., ge=0.0, le=1.0)
    non_membership: float = Field(..., ge=0.0, le=1.0)
    hesitation: float = Field(default=0.0, ge=0.0, le=1.0)
    fuzzy_family: Literal["IFS", "PFS"] = "IFS"

    @model_validator(mode="after")
    def validate_constraints(self) -> FuzzyState:
        m, n = self.membership, self.non_membership
        if self.fuzzy_family == "IFS":
            if m + n > 1.0 + 1e-5:
                raise ValueError(f"IFS violation: membership ({m}) + non-membership ({n}) must be <= 1")
            self.hesitation = max(0.0, min(1.0, 1.0 - m - n))
        elif self.fuzzy_family == "PFS":
            if m**2 + n**2 > 1.0 + 1e-5:
                raise ValueError(f"PFS violation: membership^2 ({m**2}) + non_membership^2 ({n**2}) must be <= 1")
            self.hesitation = max(0.0, min(1.0, (1.0 - m**2 - n**2)**0.5))
        return self


class SensorState(BaseRecord):
    node_id: str
    metric_name: str
    metric_value: float
    fuzzy_state: Optional[FuzzyState] = None


class GraphSnapshotManifest(BaseRecord):
    snapshot_hash: str = Field(..., description="Deterministic hash of the graph snapshot topology and attributes")
    node_counts: Dict[NodeType, int]
    edge_counts: Dict[str, int]
    parent_snapshot_hash: Optional[str] = None


class TriggerEvent(BaseRecord):
    trigger_type: str = Field(..., description="E.g., hazard_impact, node_failure, load_spike")
    target_node_id: str
    intensity: float = Field(..., ge=0.0, le=1.0)
    cascade_depth: int = 0


class CascadeLabel(BaseRecord):
    node_id: str
    task_type: Literal["binary_occurrence", "multiclass_horizon", "regression_size"]
    value: Union[int, float]


class CascadePrediction(BaseRecord):
    prediction_id: str
    node_id: str
    predicted_value: Union[float, int, List[float]]
    confidence: float = Field(..., ge=0.0, le=1.0)
    task_type: Literal["binary_occurrence", "multiclass_horizon", "regression_size"]


class BoundCertificate(BaseRecord):
    bound_type: str = Field(..., description="E.g., maximum_cascade_propagation_radius")
    theoretical_limit: float
    empirical_limit: float
    certificates_satisfied: bool


class CalibrationSummary(BaseRecord):
    metric_name: str
    expected_value: float
    observed_value: float
    variance: float


class ModelArtifactManifest(BaseRecord):
    model_class: str
    config_hash: str
    data_manifest_hash: str
    source_commit: str
    python_version: str
    torch_version: str
    cuda_version: Optional[str] = None
    task_schema: Dict[str, Any]


class PredictionTrace(BaseRecord):
    prediction_id: str
    snapshot_hash: str
    input_trigger_id: str
    visited_nodes: List[str]
    propagation_latencies: List[float]
