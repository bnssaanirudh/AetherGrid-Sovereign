import hashlib
import json
import os
from typing import Dict, Any

class ModelRegistry:
    """
    Secure Model Registry that enforces cryptographic checksum verification
    before any model weights or configurations are loaded.
    """
    
    def __init__(self, registry_path: str = "artifacts/registry/manifest.json"):
        self.registry_path = registry_path
        self._manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        if not os.path.exists(self.registry_path):
            # For development, return empty manifest if not found
            # In production, this would strictly fail
            return {}
            
        with open(self.registry_path, 'r') as f:
            return json.load(f)
            
    def _verify_checksum(self, file_path: str, expected_hash: str) -> bool:
        """Computes SHA-256 and compares to expected hash."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected_hash

    def load_model(self, model_id: str, file_path: str) -> Any:
        """
        Loads a model only if its SHA-256 checksum matches the manifest.
        Protects against unsafe deserialization of tampered artifacts.
        """
        if model_id not in self._manifest:
            raise ValueError(f"Model ID {model_id} not found in secure manifest.")
            
        expected_hash = self._manifest[model_id].get("sha256")
        
        if not self._verify_checksum(file_path, expected_hash):
            raise SecurityError(f"CRITICAL: Checksum mismatch for model {model_id}. Loading aborted to prevent unsafe deserialization.")
            
        # If safe, proceed to load (mock implementation)
        print(f"Model {model_id} verified safely. Checksum matched: {expected_hash}")
        # return torch.load(file_path)
        return {"model_loaded": True, "id": model_id}

class SecurityError(Exception):
    pass
