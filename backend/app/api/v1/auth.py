from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
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

@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
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
    import json
    import base64
    
    # Store the origin so we know where to redirect after login
    origin = request.query_params.get("from", "/dashboard")
    state_data = json.dumps({"from": origin})
    state = base64.urlsafe_b64encode(state_data.encode()).decode().rstrip('=')
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@router.get("/oauth/google/callback")
async def google_auth(request: Request, response: Response, code: str, state: str, db: AsyncSession = Depends(get_db)):
    import json
    import base64
    import httpx
    from app.models.candidate import Candidate
    
    # decode state to find origin
    origin = "/dashboard"
    try:
        padded_state = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(padded_state))
        origin = state_data.get("from", "/dashboard")
    except Exception:
        pass

    try:
        # exchange code -> tokens
        async with httpx.AsyncClient() as client:
            token_resp = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI
            })
            token_resp.raise_for_status()
            token_data = token_resp.json()
            
            # get user info
            userinfo_resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={
                "Authorization": f"Bearer {token_data['access_token']}"
            })
            userinfo_resp.raise_for_status()
            user_info = userinfo_resp.json()
            
        if not user_info or 'email' not in user_info:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
            
        email = user_info['email']
        first_name = user_info.get('given_name', 'User')
        oauth_id = user_info.get('sub')
        
        # Security: Prevent Candidates from logging into the HR portal
        candidate_result = await db.execute(select(Candidate).where(Candidate.email == email))
        if candidate_result.scalars().first():
            raise HTTPException(status_code=403, detail="Email is registered as a candidate. You cannot access the HR portal with this account.")
        
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            # Generate a signed registration token instead of passing raw parameters
            from jose import jwt
            from datetime import datetime, timedelta
            from app.core.config import settings
            
            payload = {
                "sub": email,
                "name": first_name,
                "oauth_id": oauth_id,
                "purpose": "oauth_registration",
                "exp": datetime.utcnow() + timedelta(minutes=10)
            }
            reg_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/register?reg_token={reg_token}")
        
        # Create tokens
        access_token, refresh_token = await create_tokens(db, user)
        _set_refresh_cookie(response, refresh_token)
        
        from fastapi.responses import RedirectResponse
        frontend_url = f"{settings.FRONTEND_URL}{origin}?auth=success&token={access_token}&uid={user.id}"
        return RedirectResponse(url=frontend_url)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Google authentication failed")

from app.schemas.auth import OauthRegisterRequest, OauthPreviewResponse

@router.get("/register/oauth/preview", response_model=OauthPreviewResponse)
async def preview_oauth_registration(reg_token: str):
    from jose import jwt, JWTError, ExpiredSignatureError
    from app.core.config import settings
    try:
        payload = jwt.decode(reg_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "oauth_registration":
            raise HTTPException(status_code=400, detail="Invalid token purpose")
        return {"email": payload.get("sub"), "name": payload.get("name")}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Registration token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid registration token")

@router.post("/register/oauth", response_model=Token)
async def register_oauth_endpoint(payload: OauthRegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    from jose import jwt, JWTError, ExpiredSignatureError
    from app.core.config import settings
    try:
        decoded = jwt.decode(payload.reg_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if decoded.get("purpose") != "oauth_registration":
            raise HTTPException(status_code=400, detail="Invalid token purpose")
            
        email = decoded.get("sub")
        first_name = decoded.get("name")
        oauth_id = decoded.get("oauth_id")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Registration token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid registration token")
        
    # Security: Ensure they aren't a Candidate (double check)
    from app.models.candidate import Candidate
    candidate_result = await db.execute(select(Candidate).where(Candidate.email == email))
    if candidate_result.scalars().first():
        raise HTTPException(status_code=403, detail="Email is registered as a candidate.")
        
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User already registered")
        
    # Register the user using org_name
    user = await register_oauth_user(db, email, first_name, "google", oauth_id, payload.org_name)
    
    # Issue real JWTs
    access_token, refresh_token = await create_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}
