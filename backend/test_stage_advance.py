import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job, PipelineStage
from app.models.application import Application, ApplicationStageHistory
from app.models.identity import User, Organization
from app.models.candidate import Candidate
from app.schemas.interview import InterviewCreate
from app.api.v1.interviews import create_interview

# Unique slug per run avoids any possibility of collision with leftover data
TEST_SLUG = f"test-org-{uuid.uuid4().hex[:8]}"

async def run_test():
    async with AsyncSessionLocal() as db:
        created_ids = {}
        try:
            # 1. Setup mock data
            org = Organization(name="Test Org", slug=TEST_SLUG)
            db.add(org)
            await db.flush()
            created_ids["org"] = org.id

            user = User(email=f"hr-{TEST_SLUG}@test.com", role="hr_manager", org_id=org.id)
            db.add(user)
            await db.flush()

            job = Job(title="Test Job", description="Test", org_id=org.id)
            db.add(job)
            await db.flush()

            stage1 = PipelineStage(job_id=job.id, name="Applied", order_index=1)
            stage2 = PipelineStage(job_id=job.id, name="Interviewing", order_index=2)
            db.add_all([stage1, stage2])
            await db.flush()

            candidate = Candidate(name="Test Candidate", email=f"cand-{TEST_SLUG}@test.com", source="portal")
            db.add(candidate)
            await db.flush()

            application = Application(
                job_id=job.id,
                candidate_id=candidate.id,
                current_stage_id=stage1.id,
                org_id=org.id,
                applied_at="2026-08-10T10:00:00Z"
            )
            db.add(application)
            await db.commit()

            print(f"Before create_interview: Application {application.id} is at stage {application.current_stage_id} (Applied: {stage1.id})")

            # 2. Run the endpoint function
            interview_in = InterviewCreate(
                application_id=application.id,
                interviewer_id=user.id,
                scheduled_at="2026-09-01T10:00:00Z",
                duration_minutes=30
            )

            await create_interview(interview_in=interview_in, db=db, current_user=user)

            # 3. Verify changes
            await db.refresh(application)
            print(f"After create_interview: Application {application.id} is at stage {application.current_stage_id} (Interviewing: {stage2.id})")

            assert application.current_stage_id == stage2.id, (
                f"FAIL: expected stage {stage2.id}, got {application.current_stage_id}"
            )

            history_res = await db.execute(
                select(ApplicationStageHistory)
                .where(ApplicationStageHistory.application_id == application.id)
            )
            hist = history_res.scalars().all()
            print(f"Found {len(hist)} history records:")
            for h in hist:
                print(f" - Moved from {h.from_stage_id} to {h.to_stage_id}: {h.notes}")

            assert len(hist) == 1, f"FAIL: expected 1 history record, found {len(hist)}"

            print("PASS: stage advanced correctly and history recorded.")

        finally:
            # 4. Teardown — always runs, even on assertion failure, so DB stays clean
            await db.rollback()  # discard anything not yet committed (e.g. the interview itself)
            async with AsyncSessionLocal() as cleanup_db:
                if "org" in created_ids:
                    org_row = await cleanup_db.get(Organization, created_ids["org"])
                    if org_row:
                        # Cascade-safe manual cleanup in FK-dependency order
                        await cleanup_db.execute(
                            select(Application).where(Application.org_id == created_ids["org"])
                        )
                        # Simplest robust approach: delete children first, then org
                        from sqlalchemy import delete
                        await cleanup_db.execute(delete(ApplicationStageHistory).where(
                            ApplicationStageHistory.application_id.in_(
                                select(Application.id).where(Application.org_id == created_ids["org"])
                            )
                        ))
                        await cleanup_db.execute(delete(Application).where(Application.org_id == created_ids["org"]))
                        await cleanup_db.execute(delete(PipelineStage).where(
                            PipelineStage.job_id.in_(select(Job.id).where(Job.org_id == created_ids["org"]))
                        ))
                        await cleanup_db.execute(delete(Job).where(Job.org_id == created_ids["org"]))
                        await cleanup_db.execute(delete(User).where(User.org_id == created_ids["org"]))
                        await cleanup_db.execute(delete(Organization).where(Organization.id == created_ids["org"]))
                        await cleanup_db.commit()
                        print(f"Cleanup: removed test org {TEST_SLUG} and all related rows.")

if __name__ == "__main__":
    asyncio.run(run_test())