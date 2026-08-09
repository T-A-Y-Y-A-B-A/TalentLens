from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from jose import jwt, ExpiredSignatureError, JWTError
import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User, Invite, InviteStatus
from app.schemas.invite import InviteCreate, InviteRead, InviteAccept
from app.core.config import settings
from app.core.security import enforce_role, get_password_hash
from app.workers.tasks.email import send_invite_email

router = APIRouter(prefix="/invites", tags=["invites"])

@router.post("", response_model=InviteRead)
async def create_invite(
    obj_in: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enforce_role(current_user.role.value, "invites", "manage")
    
    # Check if user with this email already exists
    result = await db.execute(select(User).where(User.email == obj_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create signed token
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    exp_str = exp.isoformat()
    
    payload = {
        "email": obj_in.email,
        "role": obj_in.role,
        "org_id": str(current_user.org_id),
        "exp": exp
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    # Create invite in DB
    db_invite = Invite(
        email=obj_in.email,
        role=obj_in.role,
        org_id=current_user.org_id,
        invited_by=current_user.id,
        token=token,
        status=InviteStatus.PENDING,
        expires_at=exp_str
    )
    db.add(db_invite)
    await db.commit()
    await db.refresh(db_invite)
    
    # Trigger Celery Task
    invite_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    send_invite_email.delay(str(db_invite.id), db_invite.email, invite_url)
    
    # Construct response
    res = InviteRead.model_validate(db_invite)
    res.link = invite_url
    return res

@router.get("", response_model=List[InviteRead])
async def list_invites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enforce_role(current_user.role.value, "invites", "manage")
    
    result = await db.execute(
        select(Invite).where(Invite.org_id == current_user.org_id).order_by(Invite.created_at.desc())
    )
    invites = result.scalars().all()
    
    # Attach links for convenience
    res_list = []
    for inv in invites:
        item = InviteRead.model_validate(inv)
        item.link = f"{settings.FRONTEND_URL}/accept-invite?token={inv.token}"
        res_list.append(item)
        
    return res_list

@router.post("/accept")
async def accept_invite(
    obj_in: InviteAccept,
    db: AsyncSession = Depends(get_db)
):
    # Decode token
    try:
        payload = jwt.decode(obj_in.token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="This invite has expired.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid invite token.")
        
    # Verify invite in DB
    result = await db.execute(select(Invite).where(Invite.token == obj_in.token))
    db_invite = result.scalars().first()
    
    if not db_invite:
        raise HTTPException(status_code=400, detail="Invite not found.")
        
    if db_invite.status == InviteStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="This invite has already been accepted.")
    elif db_invite.status == InviteStatus.REVOKED:
        raise HTTPException(status_code=400, detail="This invite has been revoked.")
    elif db_invite.status == InviteStatus.EXPIRED:
        raise HTTPException(status_code=400, detail="This invite has expired.")
        
    # Check manual expiration string just in case
    if datetime.datetime.fromisoformat(db_invite.expires_at) < datetime.datetime.now(datetime.timezone.utc):
        db_invite.status = InviteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="This invite has expired.")
        
    # Check if user already exists
    user_result = await db.execute(select(User).where(User.email == db_invite.email))
    if user_result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists.")
        
    # Create the user using token payload
    new_user = User(
        email=payload["email"],
        role=payload["role"],
        org_id=UUID(payload["org_id"]),
        hashed_password=get_password_hash(obj_in.password),
        is_verified=True
    )
    db.add(new_user)
    
    # Mark invite accepted
    db_invite.status = InviteStatus.ACCEPTED
    db_invite.accepted_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    await db.commit()
    
    return {"message": "Account created successfully."}

@router.post("/{invite_id}/revoke")
async def revoke_invite(
    invite_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enforce_role(current_user.role.value, "invites", "manage")
    
    result = await db.execute(
        select(Invite).where(Invite.id == invite_id, Invite.org_id == current_user.org_id)
    )
    db_invite = result.scalars().first()
    
    if not db_invite:
        raise HTTPException(status_code=404, detail="Invite not found")
        
    if db_invite.status != InviteStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot revoke an invite that is {db_invite.status.value}")
        
    db_invite.status = InviteStatus.REVOKED
    await db.commit()
    
    return {"message": "Invite revoked"}
