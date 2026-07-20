from fastapi import APIRouter
from typing import Dict, Any

from ..config import settings
from ..core.database import db
from ..core.queue import task_queue
from ..core.storage import storage_store

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
def health_check() -> Dict[str, Any]:
    """Returns general service health."""
    return {"status": "healthy", "version": "1.0.0"}

@router.get("/readiness", response_model=Dict[str, Any])
def readiness_check() -> Dict[str, Any]:
    """Returns detailed readyness including dependencies status."""
    dependencies = {
        "database": "online",
        "redis": "online" if task_queue.use_redis else "offline_fallback",
        "object_store": "online" if storage_store.use_minio else "offline_fallback",
    }
    
    # Try a simple DB query
    try:
        db.get_latest_snapshot()
    except Exception:
        dependencies["database"] = "error"
        
    overall = "ready" if "error" not in dependencies.values() else "unready"
    
    return {
        "status": overall,
        "dependencies": dependencies,
        "dev_mode": settings.DEV_MODE
    }
