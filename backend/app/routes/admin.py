from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.auth import RoleChecker
from ..core.audit import AuditLogger

router = APIRouter()

@router.get("/admin/audit", response_model=List[Dict[str, Any]])
def get_audit_logs(
    limit: int = 50,
    user: Dict = Depends(RoleChecker(["administrator"]))
) -> List[Dict[str, Any]]:
    """Retrieves append-only operational audit trails."""
    return AuditLogger.get_logs(limit)

class KeyRotationPayload(BaseModel):
    old_key: str = Field(..., description="Key to revoke")
    new_key: str = Field(..., description="New key to register")

@router.post("/admin/keys/rotate", response_model=Dict[str, Any])
def rotate_api_key(
    payload: KeyRotationPayload,
    user: Dict = Depends(RoleChecker(["administrator"]))
) -> Dict[str, Any]:
    """Rotates API access credentials."""
    from ..config import settings
    if payload.old_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key to rotate not found in settings registry.",
        )
    # Perform rotation (mocked local configuration update)
    settings.API_KEYS.remove(payload.old_key)
    settings.API_KEYS.append(payload.new_key)
    
    AuditLogger.log(
        action="api_key_rotated",
        actor=user.get("sub", "unknown"),
        resource_type="credentials",
        resource_id="api_keys",
        extra={"key_preview": f"{payload.new_key[:5]}..."}
    )
    
    return {
        "status": "success",
        "message": "Key credentials rotated successfully."
    }
