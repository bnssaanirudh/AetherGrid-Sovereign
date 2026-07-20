import json
import logging
import queue
import threading
from typing import Dict, Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)

class PluggableTaskQueue:
    """Redis-backed queue with a thread-safe in-process memory queue fallback."""
    def __init__(self) -> None:
        self.use_redis = settings.REDIS_URL is not None
        self.redis_client = None
        self.local_queue = queue.Queue()
        
        if self.use_redis:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis task queue connection successful.")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory queue: {e}")
                self.use_redis = False

    def enqueue(self, task_name: str, payload: Dict[str, Any]) -> None:
        data = {"task_name": task_name, "payload": payload}
        serialized = json.dumps(data)
        
        if self.use_redis:
            try:
                self.redis_client.rpush("aethergrid_tasks", serialized)
                return
            except Exception as e:
                logger.error(f"Redis enqueue failed, fallback to local queue: {e}")
                
        # Local fallback
        self.local_queue.put(data)

    def dequeue(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        if self.use_redis:
            try:
                res = self.redis_client.blpop("aethergrid_tasks", timeout=int(max(1.0, timeout)))
                if res:
                    # blpop returns a tuple (key, value)
                    return json.loads(res[1])
            except Exception as e:
                logger.error(f"Redis dequeue failed, checking local queue: {e}")
                
        # Local fallback
        try:
            return self.local_queue.get(timeout=timeout)
        except queue.Empty:
            return None

task_queue = PluggableTaskQueue()
