from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth, OAuthError

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.security import verify_access_token, redis_client
from app.core.rate_limit import limiter
from app.models.identity import User
from app.schemas.auth import (
    UserRegister, UserLogin, Token, 
    PasswordResetRequest, PasswordResetConfirm, EmailVerify, UserProfile
)
from app.services.auth import (
    register_user, authenticate_user, create_tokens, refresh_token_rotation,
    logout_user, verify_email, request_password_reset, confirm_password_reset,
    register_oauth_user
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True, 
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

@router.post("/register", response_model=UserProfile)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, user_in.email, user_in.password, user_in.org_name)
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_in: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, user_in.email, user_in.password)
    access_token, refresh_token = await create_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    old_refresh = request.cookies.get("refresh_token")
    if not old_refresh:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    access_token, new_refresh = await refresh_token_rotation(db, old_refresh)
    _set_refresh_cookie(response, new_refresh)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Invalidate refresh token
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await logout_user(db, refresh_token)
        
    # Blacklist access token
    if token:
        payload = await verify_access_token(token)
        if payload and "jti" in payload:
            jti = payload["jti"]
            # Expiry relative to current time or token expiry. Simple TTL logic
            import time
            exp = payload.get("exp", time.time() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
            ttl = int(exp - time.time())
            if ttl > 0:
                await redis_client.setex(f"blacklist:{jti}", ttl, "true")

    response.delete_cookie("refresh_token", httponly=True, secure=True, samesite="lax")
    return {"success": True}

@router.post("/verify-email")
async def verify_email_endpoint(payload: EmailVerify, db: AsyncSession = Depends(get_db)):
    await verify_email(db, payload.token)
    return {"success": True}

@router.post("/password-reset/request")
@limiter.limit("3/minute")
async def password_reset_req(request: Request, payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    await request_password_reset(db, payload.email)
    return {"success": True}

@router.post("/password-reset/confirm")
@limiter.limit("3/minute")
async def password_reset_conf(request: Request, payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    await confirm_password_reset(db, payload.token, payload.new_password)
    return {"success": True}

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/oauth/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/oauth/google/callback")
async def google_auth(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user_info = token.get('userinfo')
    if not user_info or 'email' not in user_info:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
    email = user_info['email']
    first_name = user_info.get('given_name', 'User')
    oauth_id = user_info.get('sub')
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        # Register new user
        user = await register_oauth_user(db, email, first_name, "google", oauth_id)
    
    # Create tokens
    access_token, refresh_token = await create_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)
    
    from fastapi.responses import RedirectResponse
    # Redirect to frontend dashboard with access token
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?token={access_token}")
