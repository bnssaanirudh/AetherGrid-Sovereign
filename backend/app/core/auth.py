import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import settings

security = HTTPBearer()

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Validates ingestion/service API keys."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing (X-API-Key header required).",
        )
    if x_api_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key.",
        )
    return x_api_key


# Simple HMACSigned Token generator/validator to avoid dependency blocks
def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode()
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"


def decode_access_token(token: str) -> Dict:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError()
        payload_b64, signature = parts[0], parts[1]
        
        # Verify signature
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, signature):
            raise ValueError()
            
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        
        # Verify expiration
        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired.",
            )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    # Secure Dev Mode shortcut
    if settings.DEV_MODE and token.startswith("dev-token-"):
        role = token.split("dev-token-")[1]
        valid_roles = ["viewer", "analyst", "operator", "model_approver", "data_steward", "administrator"]
        if role in valid_roles:
            return {"sub": f"dev_user_{role}", "role": role}
            
    return decode_access_token(token)


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Dict = Depends(get_current_user)) -> Dict:
        user_role = user.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role {user_role}. Required: {self.allowed_roles}",
            )
        return user
