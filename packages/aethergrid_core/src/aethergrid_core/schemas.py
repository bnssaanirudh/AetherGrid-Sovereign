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
    # Label value: int for occurrence/horizon, float for regression size
    value: Union[int, float]


class InterventionCandidate(BaseModel):
    node_id: str
    action: Literal["remove", "reinforce", "isolate", "repair"]


class ScenarioRequest(BaseRecord):
    trigger_selection: List[str] = Field(..., description="List of trigger node IDs")
    hazard_override: Optional[float] = Field(None, description="Override the hazard intensity (0-1)")
    sensor_dropout_level: float = Field(0.0, description="Fraction of sensors dropped (0-1)", ge=0.0, le=1.0)
    phase_model_variant: str = Field("default", description="Variant of phase model to apply")
    intervention_candidates: List[InterventionCandidate] = Field(default_factory=list)


class CascadePrediction(BaseRecord):
    trace_id: str = Field(..., description="Trace ID for provenance")
    predicted_occurrence: float = Field(..., description="Probability of cascade occurrence", ge=0.0, le=1.0)
    predicted_size: float = Field(..., description="Predicted size/count of cascade", ge=0.0)
    predicted_radius_graph: float = Field(..., description="Predicted radius in hops", ge=0.0)
    predicted_radius_physical: Optional[float] = Field(None, description="Predicted radius in physical units", ge=0.0)
    predicted_horizon: str = Field(..., description="E.g., short, medium, long")
    affected_nodes: Dict[str, float] = Field(default_factory=dict, description="Node ID to probability mapping")
    
    # Validation/Cert fields (reserved for Prompt 6)
    calibration_fields: Optional[Dict[str, Any]] = None
    bound_fields: Optional[Dict[str, Any]] = None
    
    # Provenance
    data_version: str
    model_version: str


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


class AbstentionRecord(BaseModel):
    reason_code: str = Field(..., description="E.g., OOD_DRIFT, MISSING_CALIBRATION, LOW_COVERAGE")
    description: str
    safe_next_actions: List[str]


class PredictionSafetyCertificate(BaseRecord):
    trace_id: str
    snapshot_hash: str
    trigger_id: str
    model_artifact_hash: str
    calibration_artifact_hash: str
    data_provenance_class: str = Field("research", description="E.g., research, production")
    fuzzy_family: str
    phase_variant: str
    
    sampler_coverage: float
    calibration_status: str = Field(..., description="E.g., calibrated, uncalibrated")
    watchdog_status: str = Field("passed", description="E.g., passed, failed")
    ood_status: str = Field("in_distribution", description="E.g., in_distribution, ood")
    
    # Mutually exclusive: either we have a prediction with intervals, or we abstained
    prediction: Optional[CascadePrediction] = None
    conformal_intervals: Optional[Dict[str, Any]] = Field(None, description="Prediction sets or intervals")
    bound_status: Optional[Dict[str, Any]] = Field(None, description="Bound mode, value, coverage status, tightness")
    
    abstention: Optional[AbstentionRecord] = None
    limitations_warning: str = Field(
        "Decision support only. Human oversight required.",
        description="Mandatory safety warning"
    )

    @model_validator(mode="after")
    def validate_exclusivity(self) -> PredictionSafetyCertificate:
        if self.prediction is not None and self.abstention is not None:
            raise ValueError("Certificate cannot contain both a prediction and an abstention record.")
        if self.prediction is None and self.abstention is None:
            raise ValueError("Certificate must contain either a prediction or an abstention record.")
        return self
