import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status

from app.models.identity import User, Organization, UserRole, RefreshToken, EmailVerification, PasswordReset
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.services.email import send_verification_email, send_password_reset_email
from app.services.organization import create_organization

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def register_user(db: AsyncSession, email: str, password: str, org_name: str) -> User:
    # Check if user exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Module 1 specs: "org_id (or org creation if first user), role defaults to hr_manager for org creators"
    org = await create_organization(db, org_name)
    
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        organization=org,
        role=UserRole.HR_MANAGER,
        is_verified=False
    )
    db.add(user)
    await db.flush()
    
    # Create verification token
    raw_token = secrets.token_urlsafe(32)
    expire_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    verification = EmailVerification(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=expire_time
    )
    db.add(verification)
    await db.commit()
    await db.refresh(user)
    
    # Trigger email (non-fatal: if broker unavailable during local dev, don't crash)
    try:
        print(f"\n[DEV MODE] Verification token for {email}: {raw_token}\n")
        send_verification_email.delay(email, raw_token)
    except Exception:
        pass  # Email will not be sent but registration still succeeds
    
    return user

async def register_oauth_user(db: AsyncSession, email: str, first_name: str, oauth_provider: str, oauth_id: str, org_name: Optional[str] = None) -> User:
    if not org_name:
        org_name = f"{first_name}'s Organization"
    org = await create_organization(db, org_name, slug_suffix=secrets.token_hex(4))
    
    user = User(
        email=email,
        hashed_password=None,
        organization=org,
        role=UserRole.HR_MANAGER,
        is_verified=True,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
        
    # Update last login
    user.last_login_at = datetime.utcnow().isoformat()
    await db.commit()
    return user

async def create_tokens(db: AsyncSession, user: User) -> Tuple[str, str]:
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"org_id": str(user.org_id), "role": user.role.value}
    )
    
    raw_refresh = secrets.token_urlsafe(64)
    expire_time = (datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_refresh),
        expires_at=expire_time
    )
    db.add(rt)
    await db.commit()
    
    return access_token, raw_refresh

async def refresh_token_rotation(db: AsyncSession, old_refresh_token: str) -> Tuple[str, str]:
    token_hash = _hash_token(old_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalars().first()
    
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if rt.revoked_at:
        # Token reuse detected! Revoke all for user as a security measure
        await db.execute(update(RefreshToken).where(RefreshToken.user_id == rt.user_id).values(revoked_at=datetime.utcnow().isoformat()))
        await db.commit()
        raise HTTPException(status_code=401, detail="Token reuse detected. All sessions revoked.")
    if datetime.fromisoformat(rt.expires_at) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")
        
    # Mark old token as revoked
    rt.revoked_at = datetime.utcnow().isoformat()
    
    # Fetch user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    # Issue new tokens
    access, new_refresh = await create_tokens(db, user)
    return access, new_refresh

async def logout_user(db: AsyncSession, refresh_token: str):
    token_hash = _hash_token(refresh_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked_at=datetime.utcnow().isoformat())
    )
    await db.commit()

async def verify_email(db: AsyncSession, token: str):
    token_hash = _hash_token(token)
    result = await db.execute(select(EmailVerification).where(EmailVerification.token_hash == token_hash))
    ev = result.scalars().first()
    
    if not ev or ev.used_at:
        raise HTTPException(status_code=400, detail="Invalid or used token")
    if datetime.fromisoformat(ev.expires_at) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
        
    ev.used_at = datetime.utcnow().isoformat()
    await db.execute(update(User).where(User.id == ev.user_id).values(is_verified=True))
    await db.commit()

async def resend_verification_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        return # Do not leak existence
    
    if user.is_verified:
        return # Already verified
        
    raw_token = secrets.token_urlsafe(32)
    expire_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    
    verification = EmailVerification(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=expire_time
    )
    db.add(verification)
    await db.commit()
    
    try:
        print(f"\n[DEV MODE] Verification token for {email}: {raw_token}\n")
        send_verification_email.delay(email, raw_token)
    except Exception:
        pass  # Non-fatal

async def request_password_reset(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        return # Do not leak existence
        
    raw_token = secrets.token_urlsafe(32)
    expire_time = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    
    pr = PasswordReset(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=expire_time
    )
    db.add(pr)
    await db.commit()
    
    try:
        send_password_reset_email.delay(email, raw_token)
    except Exception:
        pass  # Non-fatal

async def confirm_password_reset(db: AsyncSession, token: str, new_password: str):
    token_hash = _hash_token(token)
    result = await db.execute(select(PasswordReset).where(PasswordReset.token_hash == token_hash))
    pr = result.scalars().first()
    
    if not pr or pr.used_at:
        raise HTTPException(status_code=400, detail="Invalid or used token")
    if datetime.fromisoformat(pr.expires_at) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
        
    pr.used_at = datetime.utcnow().isoformat()
    
    # Update password and revoke all refresh tokens
    await db.execute(update(User).where(User.id == pr.user_id).values(hashed_password=get_password_hash(new_password)))
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == pr.user_id).values(revoked_at=datetime.utcnow().isoformat()))
    
    await db.commit()
