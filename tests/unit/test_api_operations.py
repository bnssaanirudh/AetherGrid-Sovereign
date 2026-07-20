import pytest
import os
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings
from backend.app.core.database import db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown_db():
    # Clear DB before each test
    db.clear_all_tables()
    yield

def test_health_and_readiness():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp = client.get("/api/v1/readiness")
    assert resp.status_code == 200
    assert "status" in resp.json()


def test_rbac_rules():
    # Try to access admin/audit without token -> should fail
    resp = client.get("/api/v1/admin/audit")
    assert resp.status_code == 401
    
    # Try to access admin/audit with viewer token -> should fail (forbidden)
    headers = {"Authorization": "Bearer dev-token-viewer"}
    resp = client.get("/api/v1/admin/audit", headers=headers)
    assert resp.status_code == 403

    # Try to access admin/audit with administrator token -> should succeed
    headers = {"Authorization": "Bearer dev-token-administrator"}
    resp = client.get("/api/v1/admin/audit", headers=headers)
    assert resp.status_code == 200


def test_idempotent_ingestion():
    headers = {"X-API-Key": "internal-ingestion-key-1234"}
    payload = {
        "event_id": "evt_test_1001",
        "event_type": "sensor_reading",
        "data": {"node_id": "power_0", "metric_name": "voltage", "metric_value": 0.98}
    }
    
    # First ingest
    resp = client.post("/api/v1/events/ingest", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Second duplicate ingest
    resp = client.post("/api/v1/events/ingest", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
    assert resp.json()["reason_code"] == "DUPLICATE_EVENT"


def test_watchdog_quarantine():
    headers = {"X-API-Key": "internal-ingestion-key-1234"}
    payload = {
        "event_id": "evt_test_1002",
        "event_type": "sensor_reading",
        "data": {"node_id": "power_0", "metric_name": "voltage", "fail_watchdog": True}
    }
    
    resp = client.post("/api/v1/events/ingest", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "quarantined"
    assert resp.json()["reason_code"] == "WATCHDOG_QUARANTINED"


def test_snapshot_materialization():
    headers = {"Authorization": "Bearer dev-token-operator"}
    resp = client.post("/api/v1/snapshots/materialize", headers=headers)
    assert resp.status_code == 200
    assert "snapshot_hash" in resp.json()
    assert "store_uri" in resp.json()


def test_model_lifecycle_and_rollback():
    auth_headers = {"Authorization": "Bearer dev-token-administrator"}
    
    # 1. Register Model A
    payload_a = {
        "model_id": "model_a",
        "version": "1.0.0",
        "checksum": "checksum_a_1234",
        "config": {"layers": 2, "dim": 16}
    }
    resp = client.post("/api/v1/models/register", json=payload_a, headers=auth_headers)
    assert resp.status_code == 200

    # 2. Register Model B
    payload_b = {
        "model_id": "model_b",
        "version": "1.1.0",
        "checksum": "checksum_b_5678",
        "config": {"layers": 3, "dim": 16}
    }
    resp = client.post("/api/v1/models/register", json=payload_b, headers=auth_headers)
    assert resp.status_code == 200

    # 3. Approve Model A
    resp = client.post("/api/v1/models/approve/model_a", headers=auth_headers)
    assert resp.status_code == 200

    # Get active model -> should be A
    resp = client.get("/api/v1/models/active")
    assert resp.json()["model_id"] == "model_a"

    # 4. Approve Model B (Model A gets demoted to archived)
    resp = client.post("/api/v1/models/approve/model_b", headers=auth_headers)
    assert resp.status_code == 200

    # Get active model -> should be B
    resp = client.get("/api/v1/models/active")
    assert resp.json()["model_id"] == "model_b"

    # 5. Rollback -> should set Model A back to active
    resp = client.post("/api/v1/models/rollback", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["active_model_id"] == "model_a"


def test_scenarios_prediction_inference():
    headers = {"Authorization": "Bearer dev-token-analyst"}
    payload = {
        "trigger_nodes": ["power_1"],
        "hazard_intensity": 0.85,
        "sensor_dropout": 0.1
    }

    # 1. Sync prediction before model/snapshot approved -> should return Abstention Certificate
    resp = client.post("/api/v1/scenarios/sync", json=payload, headers=headers)
    assert resp.status_code == 200
    assert "abstention" in resp.json()
    assert resp.json()["abstention"]["reason_code"] == "UNAPPROVED_MODEL"

    # Register/approve model and materialize snapshot
    admin_headers = {"Authorization": "Bearer dev-token-administrator"}
    client.post("/api/v1/models/register", json={
        "model_id": "model_test",
        "version": "1.0.0",
        "checksum": "chk_123",
        "config": {}
    }, headers=admin_headers)
    client.post("/api/v1/models/approve/model_test", headers=admin_headers)
    
    operator_headers = {"Authorization": "Bearer dev-token-operator"}
    client.post("/api/v1/snapshots/materialize", headers=operator_headers)

    # 2. Sync prediction after approved model/snapshot -> should return active prediction certificate
    resp = client.post("/api/v1/scenarios/sync", json=payload, headers=headers)
    assert resp.status_code == 200
    assert "prediction" in resp.json()
    assert "conformal_intervals" in resp.json()
    assert "bound_status" in resp.json()


def test_async_scenario_jobs():
    headers = {"Authorization": "Bearer dev-token-analyst"}
    payload = {
        "trigger_nodes": ["power_1"],
        "hazard_intensity": 0.85,
        "sensor_dropout": 0.1
    }

    # Register/approve model and materialize snapshot so task runs fine
    admin_headers = {"Authorization": "Bearer dev-token-administrator"}
    client.post("/api/v1/models/register", json={
        "model_id": "model_test",
        "version": "1.0.0",
        "checksum": "chk_123",
        "config": {}
    }, headers=admin_headers)
    client.post("/api/v1/models/approve/model_test", headers=admin_headers)
    operator_headers = {"Authorization": "Bearer dev-token-operator"}
    client.post("/api/v1/snapshots/materialize", headers=operator_headers)

    # Submit async job
    resp = client.post("/api/v1/scenarios/async", json=payload, headers=headers)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Check status (should be completed since worker runs synchronously in lifespan setup or via test runner)
    resp = client.get(f"/api/v1/scenarios/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("queued", "completed")
