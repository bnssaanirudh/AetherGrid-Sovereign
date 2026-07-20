import time
import logging
import threading
from typing import Dict, Any

from .core.queue import task_queue
from .core.database import db
from .routes.scenarios import execute_inference_pipeline, ScenarioPayload

logger = logging.getLogger(__name__)

# Control flag for local background worker threads
_worker_running = False
_worker_thread = None

def process_single_task() -> bool:
    """Dequeues and processes one task. Returns True if a task was processed, False otherwise."""
    task = task_queue.dequeue(timeout=0.5)
    if not task:
        return False
        
    task_name = task.get("task_name")
    payload = task.get("payload", {})
    
    if task_name == "run_inference":
        job_id = payload.get("job_id")
        raw_payload = payload.get("payload", {})
        
        logger.info(f"Worker picked up job: {job_id}")
        db.update_job(job_id, status="running")
        
        try:
            # Reconstruct scenario request schema
            scenario_payload = ScenarioPayload(**raw_payload)
            
            # Execute inference
            cert = execute_inference_pipeline(scenario_payload)
            
            # Mark complete
            db.update_job(
                job_id=job_id,
                status="completed",
                result_certificate=cert.model_dump(mode="json")
            )
            logger.info(f"Worker completed job successfully: {job_id}")
        except Exception as e:
            logger.error(f"Worker job {job_id} failed: {e}")
            db.update_job(
                job_id=job_id,
                status="failed",
                failure_reason=str(e)
            )
            
    return True


def _worker_loop() -> None:
    global _worker_running
    logger.info("Background worker loop started.")
    while _worker_running:
        try:
            process_single_task()
        except Exception as e:
            logger.error(f"Error in worker thread: {e}")
            time.sleep(1.0)
    logger.info("Background worker loop stopped.")


def start_worker() -> None:
    global _worker_running, _worker_thread
    if _worker_running:
        return
    _worker_running = True
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()
    logger.info("Local background worker thread spawned.")


def stop_worker() -> None:
    global _worker_running, _worker_thread
    if not _worker_running:
        return
    _worker_running = False
    if _worker_thread:
        _worker_thread.join(timeout=2.0)
    logger.info("Local background worker thread stopped.")
