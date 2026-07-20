import os
import shutil
import logging
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)

class PluggableObjectStore:
    """Pluggable S3/MinIO compatible object store with local directory fallback."""
    def __init__(self) -> None:
        self.use_minio = settings.MINIO_ENDPOINT is not None
        self.local_dir = settings.LOCAL_STORAGE_DIR
        os.makedirs(self.local_dir, exist_ok=True)
        
        if self.use_minio:
            try:
                from minio import Minio
                self.client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=False
                )
                # Ensure bucket exists
                if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                    self.client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info("MinIO storage client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize MinIO client, falling back to local storage: {e}")
                self.use_minio = False

    def put_object(self, object_name: str, file_path: str) -> str:
        """Stores file and returns location URI."""
        if self.use_minio:
            try:
                self.client.fput_object(
                    settings.MINIO_BUCKET_NAME,
                    object_name,
                    file_path
                )
                return f"minio://{settings.MINIO_BUCKET_NAME}/{object_name}"
            except Exception as e:
                logger.error(f"MinIO put failed, falling back to local copy: {e}")
        
        # Local fallback
        dest_path = os.path.join(self.local_dir, object_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy(file_path, dest_path)
        return f"file://{os.path.abspath(dest_path)}"

    def get_object(self, object_name: str, target_file_path: str) -> bool:
        """Retrieves object and writes to target_file_path."""
        if self.use_minio:
            try:
                self.client.fget_object(
                    settings.MINIO_BUCKET_NAME,
                    object_name,
                    target_file_path
                )
                return True
            except Exception as e:
                logger.error(f"MinIO get failed, trying local fallback: {e}")
                
        # Local fallback
        src_path = os.path.join(self.local_dir, object_name)
        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            if os.path.abspath(src_path) != os.path.abspath(target_file_path):
                shutil.copy(src_path, target_file_path)
            return True
        return False

storage_store = PluggableObjectStore()
