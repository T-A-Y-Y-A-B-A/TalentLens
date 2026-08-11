import uuid
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.support import Notification
from app.workers.tasks.interview_email import send_interview_invite_email
import asyncio

def check():
    candidate_id = "00000000-0000-0000-0000-000000000001"
    
    print("Running send_interview_invite_email...")
    send_interview_invite_email(
        interview_id=str(uuid.uuid4()),
        candidate_email="test@test.com",
        interviewer_email="interviewer@test.com",
        candidate_name="Test Cand",
        interviewer_name="Interviewer",
        job_title="Software Engineer",
        scheduled_at="2026-10-10T10:00:00Z",
        duration_minutes=30,
        candidate_id=candidate_id
    )
    
    print("Checking DB for notification...")
    async def get_notifs():
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Notification).where(Notification.recipient_id == candidate_id))
            notifs = res.scalars().all()
            for n in notifs:
                print(f"Found notification: {n.type}, payload: {n.payload}")
            if not notifs:
                print("No notifications found!")

    asyncio.run(get_notifs())

if __name__ == "__main__":
    check()
