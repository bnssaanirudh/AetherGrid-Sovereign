import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.auth import RoleChecker
from ..core.database import db
from ..core.audit import AuditLogger

router = APIRouter()

class RegisterModelPayload(BaseModel):
    model_id: str = Field(..., description="Unique model identifier")
    version: str = Field(..., description="Semantic version string")
    checksum: str = Field(..., description="SHA-256 checksum of model artifact")
    config: Dict[str, Any] = Field(..., description="Architecture parameters")

@router.post("/models/register", response_model=Dict[str, Any])
def register_model(
    payload: RegisterModelPayload,
    user: Dict = Depends(RoleChecker(["analyst", "administrator"]))
) -> Dict[str, Any]:
    """Registers a model artifact with checksum verification."""
    # Check if duplicate
    existing = db.get_model(payload.model_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model {payload.model_id} already registered.",
        )
        
    db.insert_model(
        model_id=payload.model_id,
        version=payload.version,
        checksum=payload.checksum,
        config=payload.config,
        status="registered"
    )
    
    AuditLogger.log(
        action="model_registered",
        actor=user.get("sub", "unknown"),
        resource_type="model",
        resource_id=payload.model_id
    )
    
    return {
        "status": "success",
        "model_id": payload.model_id,
        "version": payload.version,
        "checksum": payload.checksum,
    }


@router.post("/models/approve/{model_id}", response_model=Dict[str, Any])
def approve_model(
    model_id: str,
    user: Dict = Depends(RoleChecker(["model_approver", "administrator"]))
) -> Dict[str, Any]:
    """Approves a model artifact, setting it as active. Demotes the previous active model."""
    model = db.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found.",
        )
        
    # Get currently active model to demote
    current_active = db.get_model_by_status("active")
    if current_active:
        db.insert_model(
            model_id=current_active["model_id"],
            version=current_active["version"],
            checksum=current_active["checksum"],
            config=current_active["config_json"],
            status="archived"
        )
        
    # Set this model as active
    db.insert_model(
        model_id=model["model_id"],
        version=model["version"],
        checksum=model["checksum"],
        config=model["config_json"],
        status="active"
    )
    
    AuditLogger.log(
        action="model_approved",
        actor=user.get("sub", "unknown"),
        resource_type="model",
        resource_id=model_id
    )
    
    return {
        "status": "success",
        "message": f"Model {model_id} is now set as the active serving model.",
        "previous_active": current_active["model_id"] if current_active else None
    }


@router.post("/models/rollback", response_model=Dict[str, Any])
def rollback_model(
    user: Dict = Depends(RoleChecker(["operator", "administrator"]))
) -> Dict[str, Any]:
    """Rolls back the active model to the previous approved/archived model artifact."""
    current_active = db.get_model_by_status("active")
    
    # Get latest archived model
    previous = db.get_model_by_status("archived")
    if not previous:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No previous archived model available for rollback.",
        )
        
    # Mark current active as archived
    if current_active:
        db.insert_model(
            model_id=current_active["model_id"],
            version=current_active["version"],
            checksum=current_active["checksum"],
            config=current_active["config_json"],
            status="archived"
        )
        
    # Mark previous as active
    db.insert_model(
        model_id=previous["model_id"],
        version=previous["version"],
        checksum=previous["checksum"],
        config=previous["config_json"],
        status="active"
    )
    
    AuditLogger.log(
        action="model_rollback",
        actor=user.get("sub", "unknown"),
        resource_type="model",
        resource_id=previous["model_id"],
        extra={"demoted_model": current_active["model_id"] if current_active else None}
    )
    
    return {
        "status": "success",
        "active_model_id": previous["model_id"],
        "active_version": previous["version"],
        "checksum": previous["checksum"]
    }


@router.get("/models/active", response_model=Dict[str, Any])
def get_active_model() -> Dict[str, Any]:
    """Retrieves metadata of the currently active model."""
    active = db.get_model_by_status("active")
    if not active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model serving currently.",
        )
    return active
