import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from .database import db

logger = logging.getLogger("AuditLogger")

# Configure structured audit log file
AUDIT_LOG_FILE = "logs/audit.jsonl"
os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)

class AuditLogger:
    @staticmethod
    def log(action: str, actor: str, resource_type: str, resource_id: str, extra: Dict[str, Any] = None) -> None:
        """Appends structured audit log to database and file."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        payload = {
            "timestamp": timestamp,
            "action": action,
            "actor": actor,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": extra or {},
        }
        
        # Write to JSONLines file
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to audit log file: {e}")
            
        # Write to SQL db
        try:
            db.insert_audit(
                action=action,
                actor=actor,
                resource_type=resource_type,
                resource_id=resource_id
            )
        except Exception as e:
            logger.error(f"Failed to insert audit log into database: {e}")

    @staticmethod
    def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
        return db.get_audit_logs(limit)
