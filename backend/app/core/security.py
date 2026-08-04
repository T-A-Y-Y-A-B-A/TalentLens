import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional
import bcrypt
from jose import jwt, JWTError
import casbin
import redis.asyncio as redis
import uuid

from app.core.config import settings

# Redis client for token blacklisting
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# JWT
def _get_secret_key() -> str:
    # Resolution: Environment -> Fallback to random if not set
    # As per Secure Web Backend guidelines
    if settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "CHANGE_ME_IN_PROD":
        return settings.JWT_SECRET_KEY
    # Generate ephemeral secret if fallback is used in testing/dev
    return secrets.token_hex(32)

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None, additional_claims: dict = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid.uuid4())}
    if additional_claims:
        to_encode.update(additional_claims)
        
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def verify_access_token(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, _get_secret_key(), algorithms=[settings.JWT_ALGORITHM])
        jti = decoded_token.get("jti")
        if jti:
            is_blacklisted = await redis_client.get(f"blacklist:{jti}")
            if is_blacklisted:
                return None
        return decoded_token
    except JWTError:
        return None

# Casbin
_enforcer: Optional[casbin.Enforcer] = None

def get_casbin_enforcer() -> casbin.Enforcer:
    global _enforcer
    if _enforcer is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "rbac_model.conf")
        policy_path = os.path.join(base_dir, "rbac_policy.csv")
        _enforcer = casbin.Enforcer(model_path, policy_path)
    return _enforcer

from fastapi import HTTPException, status

def enforce_role(role_value: str, resource: str, action: str):
    enforcer = get_casbin_enforcer()
    if not enforcer.enforce(role_value, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to {action} on {resource}."
        )
