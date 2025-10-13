from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Optional authentication - can be disabled via settings
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token (optional authentication)
    Returns None if authentication is disabled or no token provided
    """
    if not settings.enable_auth:
        # Authentication disabled - return anonymous user
        return {
            "user_id": "anonymous",
            "username": "anonymous",
            "roles": ["user"]
        }
    
    if not credentials:
        # No token provided but auth is enabled
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username", "unknown"),
            "roles": payload.get("roles", ["user"]),
            "exp": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(user_id: str, username: str, roles: list = None) -> str:
    """Create JWT access token for user"""
    if not settings.jwt_secret:
        raise ValueError("JWT secret not configured")
    
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles or ["user"],
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")