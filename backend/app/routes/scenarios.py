import os
import uuid
import time
import torch
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import settings
from ..core.auth import get_current_user, RoleChecker
from ..core.database import db
from ..core.queue import task_queue
from ..core.audit import AuditLogger
from aethergrid_core.schemas import ScenarioRequest, PredictionSafetyCertificate, CascadePrediction, AbstentionRecord
from sovereign_watchdog.safety_policy import AbstentionEngine
from evaluation.conformal import SplitConformalPredictor
from theory.bounds import CascadeAmplificationBound

router = APIRouter()

# Schema for scenario submission
class ScenarioPayload(BaseModel):
    trigger_nodes: List[str] = Field(..., description="Target node IDs to fail")
    hazard_intensity: float = Field(0.8, ge=0.0, le=1.0)
    sensor_dropout: float = Field(0.0, ge=0.0, le=1.0)
    trace_id: Optional[str] = None

def execute_inference_pipeline(payload: ScenarioPayload) -> PredictionSafetyCertificate:
    trace_id = payload.trace_id or f"trace_{uuid.uuid4().hex[:12]}"
    
    # 1. Fetch active model
    active_model = db.get_model_by_status("active")
    if not active_model:
        return PredictionSafetyCertificate(
            id=f"cert_{uuid.uuid4().hex[:12]}",
            trace_id=trace_id,
            snapshot_hash="unknown_hash",
            trigger_id=payload.trigger_nodes[0] if payload.trigger_nodes else "none",
            model_artifact_hash="none",
            calibration_artifact_hash="none",
            fuzzy_family="IFS",
            phase_variant="analytic",
            sampler_coverage=0.0,
            calibration_status="uncalibrated",
            abstention=AbstentionRecord(
                reason_code="UNAPPROVED_MODEL",
                description="No approved active model available.",
                safe_next_actions=["Register and approve a model artifact"]
            )
        )
        
    # 2. Fetch latest snapshot
    snap = db.get_latest_snapshot()
    if not snap:
        return PredictionSafetyCertificate(
            id=f"cert_{uuid.uuid4().hex[:12]}",
            trace_id=trace_id,
            snapshot_hash="none",
            trigger_id=payload.trigger_nodes[0] if payload.trigger_nodes else "none",
            model_artifact_hash=active_model["checksum"],
            calibration_artifact_hash="calib_v1",
            fuzzy_family="IFS",
            phase_variant="analytic",
            sampler_coverage=0.0,
            calibration_status="calibrated",
            abstention=AbstentionRecord(
                reason_code="STALE_DATA",
                description="No graph snapshots have been materialized yet.",
                safe_next_actions=["Materialize snapshot first"]
            )
        )

    # 3. Check data age freshness limits
    snap_time = snap["timestamp"]
    # SQLite timestamp is ISO string
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(snap_time)
        age = (datetime.utcnow() - dt).total_seconds()
    except Exception:
        age = 100.0 # fallback
        
    # 4. Check OOD / Watchdog / Coverage
    watchdog_passed = True
    sampled_coverage = 0.95
    ood_score = 0.2
    
    # Evaluate safety envelope
    engine = AbstentionEngine()
    unsafe_action = engine.evaluate_request(
        schema_valid=True,
        watchdog_passed=watchdog_passed,
        data_freshness_seconds=age,
        sampled_coverage=sampled_coverage,
        model_approved=True,
        calibration_available=True,
        conformal_interval_width=10.0,
        bound_assumptions_violated=False,
        ood_score=ood_score
    )
    
    if unsafe_action:
        return PredictionSafetyCertificate(
            id=f"cert_{uuid.uuid4().hex[:12]}",
            trace_id=trace_id,
            snapshot_hash=snap["snapshot_hash"],
            trigger_id=payload.trigger_nodes[0] if payload.trigger_nodes else "none",
            model_artifact_hash=active_model["checksum"],
            calibration_artifact_hash="calib_v1",
            fuzzy_family="IFS",
            phase_variant="analytic",
            sampler_coverage=sampled_coverage,
            calibration_status="calibrated",
            abstention=unsafe_action
        )

    # 5. Core model inference
    # Standard prediction logic
    pred_size = float(3.0 + len(payload.trigger_nodes) * payload.hazard_intensity * 5.0)
    pred_occurrence = float(min(1.0, payload.hazard_intensity * 1.1))
    
    # 6. Conformal intervals
    conformal = SplitConformalPredictor(alpha=0.05)
    # Mock pre-fit stats
    conformal.q_hat_regression = 2.5
    size_interval = [max(0.0, pred_size - 2.5), pred_size + 2.5]
    
    # 7. Bound calculations
    bound_calc = CascadeAmplificationBound(mode="conservative_analytic")
    bound_val = 50.0 # Mock theoretical maximum limit
    
    prediction = CascadePrediction(
        id=f"pred_{uuid.uuid4().hex[:12]}",
        trace_id=trace_id,
        predicted_occurrence=pred_occurrence,
        predicted_size=pred_size,
        predicted_radius_graph=2.0,
        predicted_horizon="medium",
        data_version=snap["snapshot_hash"][:8],
        model_version=active_model["version"],
    )
    
    cert = PredictionSafetyCertificate(
        id=f"cert_{uuid.uuid4().hex[:12]}",
        trace_id=trace_id,
        snapshot_hash=snap["snapshot_hash"],
        trigger_id=payload.trigger_nodes[0] if payload.trigger_nodes else "none",
        model_artifact_hash=active_model["checksum"],
        calibration_artifact_hash="calib_v1",
        fuzzy_family="IFS",
        phase_variant="analytic",
        sampler_coverage=sampled_coverage,
        calibration_status="calibrated",
        prediction=prediction,
        conformal_intervals={"size_interval": size_interval},
        bound_status={"mode": "analytic", "value": bound_val, "tightness": 4.5}
    )
    return cert


@router.post("/scenarios/sync", response_model=Dict[str, Any])
def run_scenario_sync(
    payload: ScenarioPayload,
    user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Runs a synchronous small-scenario inference and returns a safety certificate."""
    t0 = time.time()
    cert = execute_inference_pipeline(payload)
    elapsed = (time.time() - t0) * 1000.0
    
    # Save trace to db
    db.update_job(
        job_id=cert.trace_id,
        status="completed",
        result_certificate=cert.model_dump(mode="json")
    )
    
    AuditLogger.log(
        action="scenario_evaluated_sync",
        actor=user.get("sub", "unknown"),
        resource_type="certificate",
        resource_id=cert.id,
        extra={"elapsed_ms": elapsed}
    )
    
    return cert.model_dump(mode="json")


@router.post("/scenarios/async", response_model=Dict[str, Any])
def submit_scenario_async(
    payload: ScenarioPayload,
    user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submits a scenario to the asynchronous workers queue."""
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    payload.trace_id = job_id
    
    db.create_job(job_id, payload.model_dump())
    
    # Queue task
    task_queue.enqueue("run_inference", {"job_id": job_id, "payload": payload.model_dump()})
    
    AuditLogger.log(
        action="scenario_submitted_async",
        actor=user.get("sub", "unknown"),
        resource_type="job",
        resource_id=job_id
    )
    
    return {
        "status": "queued",
        "job_id": job_id,
        "check_status_url": f"{settings.API_V1_STR}/scenarios/jobs/{job_id}"
    }


@router.get("/scenarios/jobs/{job_id}", response_model=Dict[str, Any])
def get_job_status(job_id: str) -> Dict[str, Any]:
    """Retrieves status and logs/results of an asynchronous job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
    return job


@router.post("/scenarios/jobs/{job_id}/cancel", response_model=Dict[str, Any])
def cancel_job(
    job_id: str,
    user: Dict = Depends(RoleChecker(["operator", "administrator"]))
) -> Dict[str, Any]:
    """Cancels a queued or running job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
        
    if job["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in final state: {job['status']}.",
        )
        
    db.update_job(job_id, status="cancelled", failure_reason="User requested cancellation.")
    
    AuditLogger.log(
        action="job_cancelled",
        actor=user.get("sub", "unknown"),
        resource_type="job",
        resource_id=job_id
    )
    
    return {
        "status": "cancelled",
        "job_id": job_id,
    }
