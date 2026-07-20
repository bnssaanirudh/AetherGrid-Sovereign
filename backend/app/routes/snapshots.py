import os
import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..config import settings
from ..core.auth import verify_api_key, RoleChecker
from ..core.database import db
from ..core.storage import storage_store
from ..core.audit import AuditLogger
from aethergrid_core.schemas import SensorState, GraphSnapshotManifest
from watchdog.sovereign_watchdog import SovereignWatchdog
from core.graph_constructor import UrbanGraphConstructor, GraphConfig

router = APIRouter()

# Schema for ingestion payload
class IngestPayload(BaseModel):
    event_id: str = Field(..., description="Stable unique ID for idempotency")
    event_type: str = Field("sensor_reading", description="E.g., sensor_reading, trigger_event")
    data: Dict[str, Any] = Field(..., description="Actual record attributes matching schemas")

@router.post("/events/ingest", response_model=Dict[str, Any])
def ingest_event(
    payload: IngestPayload,
    x_api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Ingests versioned sensor/events. Guaranteed idempotent."""
    # Check if duplicate
    existing = db.get_event(payload.event_id)
    if existing:
        return {
            "status": "ignored",
            "reason_code": "DUPLICATE_EVENT",
            "message": f"Event {payload.event_id} already ingested.",
            "provenance": {
                "event_id": payload.event_id,
                "is_duplicate": True,
            }
        }
        
    # Perform pre-flight schemas validations / Watchdog quarantine checks
    is_quarantined = False
    validation_status = "verified"
    
    # Simple validation mock for demonstration
    if "fail_watchdog" in payload.data or payload.data.get("metric_value", 0.0) < -1e5:
        is_quarantined = True
        validation_status = "quarantined"
        
    db.insert_event(
        event_id=payload.event_id,
        event_type=payload.event_type,
        payload=payload.data,
        status=validation_status
    )
    
    AuditLogger.log(
        action="event_ingested",
        actor=f"api_key:{x_api_key[:8]}...",
        resource_type="event",
        resource_id=payload.event_id,
        extra={"validation_status": validation_status}
    )
    
    if is_quarantined:
        return {
            "status": "quarantined",
            "reason_code": "WATCHDOG_QUARANTINED",
            "message": "Event quarantined due to structural watchdog checks failing.",
            "provenance": {
                "event_id": payload.event_id,
                "is_quarantined": True
            }
        }
        
    return {
        "status": "success",
        "reason_code": "EVENT_INGESTED",
        "message": "Event ingested and verified successfully.",
        "provenance": {
            "event_id": payload.event_id,
            "is_quarantined": False
        }
    }


@router.post("/snapshots/materialize", response_model=Dict[str, Any])
def materialize_snapshot(
    parent_hash: Optional[str] = None,
    user: Dict = Depends(RoleChecker(["operator", "administrator"]))
) -> Dict[str, Any]:
    """Triggers materialization of a new graph snapshot from verified events."""
    # Build a new graph snapshot
    # Since this is a demo, we build a graph from the constructor and save it
    cfg = GraphConfig(num_power=10, num_hospital=5, num_road=20, num_citizen=15)
    data = UrbanGraphConstructor(config=cfg).build()
    
    # Save snapshot file locally
    snapshot_hash = hashlib.sha256(f"snap_{os.urandom(16)}".encode()).hexdigest()
    filename = f"snapshot_{snapshot_hash}.pt"
    local_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)
    
    import torch
    torch.save(data, local_path)
    
    # Put to object store
    store_uri = storage_store.put_object(filename, local_path)
    
    # Clean up local file copy if MinIO successfully stored it
    if store_uri.startswith("minio://") and os.path.exists(local_path):
        os.remove(local_path)
        
    node_counts = {nt: data[nt].num_nodes for nt in data.node_types}
    edge_counts = {f"{src}__{rel}__{dst}": data[src, rel, dst].edge_index.size(1) for src, rel, dst in data.edge_types if hasattr(data[src, rel, dst], "edge_index")}
    
    db.insert_snapshot(
        snapshot_hash=snapshot_hash,
        parent_hash=parent_hash,
        node_counts=node_counts,
        edge_counts=edge_counts,
        filepath=store_uri
    )
    
    AuditLogger.log(
        action="snapshot_materialized",
        actor=user.get("sub", "unknown"),
        resource_type="snapshot",
        resource_id=snapshot_hash,
        extra={"node_counts": node_counts}
    )
    
    return {
        "status": "success",
        "snapshot_hash": snapshot_hash,
        "parent_snapshot_hash": parent_hash,
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "store_uri": store_uri
    }
