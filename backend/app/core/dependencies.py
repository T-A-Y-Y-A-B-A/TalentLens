from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_access_token, enforce_role
from app.models.identity import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = await verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
        
    return user

def require_permission(resource: str, action: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        enforce_role(current_user.role.value, resource, action)
        return current_user
    return permission_checker

async def get_current_candidate(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    from app.models.candidate import Candidate
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate candidate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = await verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    candidate_id = payload.get("sub")
    if candidate_id is None:
        raise credentials_exception
        
    # verify role explicitly is candidate
    if payload.get("role") != "candidate":
        raise credentials_exception
        
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .where(Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    if candidate is None:
        raise credentials_exception
        
    return candidate

async def get_current_candidate_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db)
):
    from app.models.candidate import Candidate
    if token is None:
        return None
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate candidate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = await verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    candidate_id = payload.get("sub")
    if candidate_id is None:
        raise credentials_exception
        
    if payload.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a candidate token"
        )
        
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .where(Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    if candidate is None:
        raise credentials_exception
        
    return candidate
