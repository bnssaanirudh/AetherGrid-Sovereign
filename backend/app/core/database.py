import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages connections and basic CRUD for API metadata."""
    def __init__(self) -> None:
        self.db_file = settings.LOCAL_DB_FILE
        self._init_db()

    def _get_conn(self):
        # We use sqlite3 for local development/fallback simplicity
        # If postgres is set, we could use psycopg2, but fallback to SQLite makes
        # direct test running zero-dependency.
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Events Ingestion table (idempotent by event_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Graph Snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_hash TEXT PRIMARY KEY,
                parent_snapshot_hash TEXT,
                node_counts TEXT NOT NULL,
                edge_counts TEXT NOT NULL,
                filepath TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Jobs queue metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                request_payload TEXT NOT NULL,
                result_certificate TEXT,
                failure_reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # Approved Models registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                checksum TEXT NOT NULL,
                config_json TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Append-only audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def clear_all_tables(self) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        for tbl in ["events", "snapshots", "jobs", "models", "audit_logs"]:
            cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
        conn.commit()
        conn.close()
        self._init_db()

    # Ingestion operations
    def insert_event(self, event_id: str, event_type: str, payload: Dict[str, Any], status: str) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO events (event_id, event_type, payload, validation_status, timestamp) VALUES (?, ?, ?, ?, ?)",
                (event_id, event_type, json.dumps(payload), status, datetime.utcnow().isoformat())
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Duplicate event
        finally:
            conn.close()

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    # Snapshot operations
    def insert_snapshot(self, snapshot_hash: str, parent_hash: Optional[str], node_counts: Dict[str, int], edge_counts: Dict[str, int], filepath: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO snapshots (snapshot_hash, parent_snapshot_hash, node_counts, edge_counts, filepath, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (snapshot_hash, parent_hash, json.dumps(node_counts), json.dumps(edge_counts), filepath, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT 1").fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    # Jobs operations
    def create_job(self, job_id: str, request_payload: Dict[str, Any]) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (job_id, status, request_payload, timestamp) VALUES (?, ?, ?, ?)",
            (job_id, "queued", json.dumps(request_payload), datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def update_job(self, job_id: str, status: str, result_certificate: Optional[Dict[str, Any]] = None, failure_reason: Optional[str] = None) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cert_json = json.dumps(result_certificate) if result_certificate else None
        cursor.execute(
            "UPDATE jobs SET status = ?, result_certificate = ?, failure_reason = ? WHERE job_id = ?",
            (status, cert_json, failure_reason, job_id)
        )
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        conn.close()
        if row:
            res = dict(row)
            res["request_payload"] = json.loads(res["request_payload"])
            if res["result_certificate"]:
                res["result_certificate"] = json.loads(res["result_certificate"])
            return res
        return None

    # Model operations
    def insert_model(self, model_id: str, version: str, checksum: str, config: Dict[str, Any], status: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO models (model_id, version, checksum, config_json, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (model_id, version, checksum, json.dumps(config), status, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def get_model_by_status(self, status: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM models WHERE status = ? ORDER BY timestamp DESC LIMIT 1", (status,)).fetchone()
        conn.close()
        if row:
            res = dict(row)
            res["config_json"] = json.loads(res["config_json"])
            return res
        return None

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM models WHERE model_id = ?", (model_id,)).fetchone()
        conn.close()
        if row:
            res = dict(row)
            res["config_json"] = json.loads(res["config_json"])
            return res
        return None

    # Audit operations
    def insert_audit(self, action: str, actor: str, resource_type: str, resource_id: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (action, actor, resource_type, resource_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (action, actor, resource_type, resource_id, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

db = DatabaseConnection()
