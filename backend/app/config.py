import os
from typing import List, Optional

class Settings:
    def __init__(self):
        self.API_V1_STR: str = "/api/v1"
        self.PROJECT_NAME: str = "AetherGrid-Sovereign API"
        
        # Auth & Security
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkeychangeinproduction")
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.DEV_MODE: bool = os.getenv("DEV_MODE", "True").lower() == "true"
        
        keys_str = os.getenv("API_KEYS", "internal-ingestion-key-1234,analyst-service-key-abcd")
        self.API_KEYS: List[str] = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        # Infrastructure Connections
        self.POSTGRES_DSN: Optional[str] = os.getenv("POSTGRES_DSN", None)
        self.REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
        self.MINIO_ENDPOINT: Optional[str] = os.getenv("MINIO_ENDPOINT", None)
        self.MINIO_ACCESS_KEY: Optional[str] = os.getenv("MINIO_ACCESS_KEY", None)
        self.MINIO_SECRET_KEY: Optional[str] = os.getenv("MINIO_SECRET_KEY", None)
        self.MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "aethergrid")
        
        # Local Storage Fallback Directories
        self.LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "data/local_storage")
        self.LOCAL_DB_FILE: str = os.getenv("LOCAL_DB_FILE", "data/metadata.db")
        
        # SLOs and Bounded parameters
        self.MAX_EGO_SUBGRAPH_HOPS: int = int(os.getenv("MAX_EGO_SUBGRAPH_HOPS", "3"))
        self.INFERENCE_TIMEOUT_SECONDS: float = float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "2.0"))
        self.DATA_FRESHNESS_LIMIT_SECONDS: int = int(os.getenv("DATA_FRESHNESS_LIMIT_SECONDS", "3600"))
        
        # Monitoring & Drift
        self.DRIFT_MIN_SAMPLE_SIZE: int = int(os.getenv("DRIFT_MIN_SAMPLE_SIZE", "50"))
        self.DRIFT_THRESHOLD_KS: float = float(os.getenv("DRIFT_THRESHOLD_KS", "0.05"))

settings = Settings()

# Ensure local directories exist
os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOCAL_DB_FILE), exist_ok=True)
