import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.identity import User, UserRole, Organization
from app.core.security import get_password_hash
import uuid

async def create_super_admin(email: str, password: str):
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User with email '{email}' already exists. Updating to super admin and changing password...")
            user.is_platform_admin = True
            user.hashed_password = get_password_hash(password)
        else:
            # We need an organization for the user, let's get or create a default one
            org_result = await db.execute(select(Organization).where(Organization.slug == "admin-org"))
            org = org_result.scalar_one_or_none()
            if not org:
                org = Organization(name="Admin Organization", slug="admin-org")
                db.add(org)
                await db.flush()
                
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                role=UserRole.SUPER_ADMIN,
                is_platform_admin=True,
                is_verified=True,
                organization=org
            )
            db.add(user)
            
        await db.commit()
        print(f"Success! Super admin created/updated.")
        print(f"Email: {email}")
        print(f"Password: {password}")

if __name__ == "__main__":
    email = "admin@talentlens.com"
    password = "admin1245!"
    
    if len(sys.argv) == 3:
        email = sys.argv[1]
        password = sys.argv[2]
        
    print(f"Creating super admin with email: {email}...")
    asyncio.run(create_super_admin(email, password))
