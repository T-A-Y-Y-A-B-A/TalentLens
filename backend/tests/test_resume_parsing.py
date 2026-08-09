import pytest
import uuid
import os
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.candidate import Candidate, Resume, ParseStatus, ResumeParsedData, CandidateEmbedding
from app.schemas.candidate import ResumeExtraction, Experience, Education
from app.ai.embeddings import EMBEDDING_MODEL_NAME

from app.models.identity import User, UserRole

@pytest.fixture
async def setup_users(async_client: AsyncClient, db_session: AsyncSession):
    # Org A: HR Manager
    email_hr_a = f"hra_{uuid.uuid4().hex[:8]}@a.com"
    org_a = f"Org A {uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/auth/register", json={"email": email_hr_a, "password": "Pass123!", "org_name": org_a})
    
    # Org B: HR Manager
    email_hr_b = f"hrb_{uuid.uuid4().hex[:8]}@b.com"
    org_b = f"Org B {uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/auth/register", json={"email": email_hr_b, "password": "Pass123!", "org_name": org_b})
    
    users = []
    for email in [email_hr_a, email_hr_b]:
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
        db_user.role = UserRole.HR_MANAGER
        users.append(db_user)
    
    await db_session.commit()
    
    async def login(email):
        resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": "Pass123!"})
        return resp.json()["access_token"]
        
    token_hr_a = await login(email_hr_a)
    token_hr_b = await login(email_hr_b)
    
    return {
        "hr_a": {"headers": {"Authorization": f"Bearer {token_hr_a}"}},
        "hr_b": {"headers": {"Authorization": f"Bearer {token_hr_b}"}}
    }

@pytest.fixture
async def setup_candidate_data(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    # Create Candidate A for Org A
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "candA@example.com",
        "name": "Candidate A"
    }, headers=headers_hr_a)
    cand_a_id = resp.json()["id"]
    
    return {
        "cand_a_id": cand_a_id
    }

@pytest.mark.asyncio
async def test_tenant_isolation_resume_download(async_client: AsyncClient, setup_users, setup_candidate_data, db_session: AsyncSession):
    headers_hr_a = setup_users["hr_a"]["headers"]
    headers_hr_b = setup_users["hr_b"]["headers"]
    cand_a_id = setup_candidate_data["cand_a_id"]
    
    # HR A creates a resume record manually for testing
    resume_id = uuid.uuid4()
    db_resume = Resume(
        id=resume_id,
        candidate_id=cand_a_id,
        file_url="fake/path.pdf",
        parse_status=ParseStatus.DONE
    )
    db_session.add(db_resume)
    await db_session.commit()
    
    # HR B tries to download the resume
    resp = await async_client.get(f"/api/v1/candidates/{cand_a_id}/resume/{resume_id}/download", headers=headers_hr_b)
    # The candidate itself won't be found because candidate is org_id isolated
    assert resp.status_code == 404

@pytest.mark.asyncio
@patch("app.workers.tasks.resume_parser.parse_resume.delay")
async def test_upload_resume_api(mock_delay, async_client: AsyncClient, setup_users, setup_candidate_data):
    headers_hr_a = setup_users["hr_a"]["headers"]
    cand_a_id = setup_candidate_data["cand_a_id"]
    
    # We will upload a dummy file
    dummy_pdf_content = b"%PDF-1.4 dummy content"
    files = {"file": ("test.pdf", dummy_pdf_content, "application/pdf")}
    
    resp = await async_client.post(f"/api/v1/candidates/{cand_a_id}/resume", headers=headers_hr_a, files=files)
    assert resp.status_code == 202
    data = resp.json()
    assert data["candidate_id"] == cand_a_id
    assert data["parse_status"] == "pending"
    assert data["file_url"].endswith(".pdf")
    
    # Ensure Celery task was triggered
    mock_delay.assert_called_once_with(data["id"])

@pytest.mark.asyncio
@patch("app.workers.tasks.resume_parser.call_llm")
@patch("app.workers.tasks.resume_parser.qdrant_client")
@patch("app.workers.tasks.resume_parser.embed_text")
@patch("app.workers.tasks.resume_parser.AsyncSessionLocal")
async def test_resume_parser_happy_path(
    mock_session_local,
    mock_embed_text,
    mock_qdrant,
    mock_call_llm,
    async_client: AsyncClient,
    setup_users,
    setup_candidate_data,
    db_session: AsyncSession
):
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def get_mock_session():
        yield db_session
    mock_session_local.return_value = get_mock_session()
    
    from app.workers.tasks.resume_parser import async_parse_resume
    import aiofiles
    
    cand_a_id = setup_candidate_data["cand_a_id"]
    
    # 1. Setup mocks
    # Mock LLM output
    async def get_mock_llm_result(*args, **kwargs):
        return ResumeExtraction(
            name="Test User",
            email="test@test.com",
            skills=["Python", "SQL"],
            experience=[],
            education=[],
            certifications=[],
            projects=[]
        )
    mock_call_llm.side_effect = get_mock_llm_result
    
    # Mock embeddings
    mock_embed_text.return_value = [0.1] * 384
    
    # Mock Qdrant upsert
    mock_qdrant.upsert = AsyncMock()
    
    # 2. Setup a valid PDF file in the uploads dir so pypdf doesn't crash on it
    # We create a simple valid PDF or we can just mock pypdf/docling
    # 2. Setup a valid PDF file in the uploads dir so pypdf doesn't crash on it
    with patch("app.workers.tasks.resume_parser.open") as mock_open:
        mock_file = MagicMock()
        mock_file.read.return_value = b"%PDF-1.4 Fake PDF content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Instead of dealing with pypdf parsing binary, let's just mock the converter / fallback block entirely
        with patch("pypdf.PdfReader") as mock_pdfreader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Fake PDF text"
            mock_pdfreader.return_value.pages = [mock_page]
            
            # Create resume in db
            resume_id = uuid.uuid4()
            db_resume = Resume(
                id=resume_id,
                candidate_id=cand_a_id,
                file_url="fake_local_path.pdf",
                parse_status=ParseStatus.PENDING
            )
            db_session.add(db_resume)
            await db_session.commit()
            
            # Run the parser async
            await async_parse_resume(str(resume_id))
            
    # 3. Assertions
    await db_session.refresh(db_resume)
    assert db_resume.parse_status == ParseStatus.DONE
    assert db_resume.raw_text == "Fake PDF text\n"
    
    # Verify parsed data
    result = await db_session.execute(select(ResumeParsedData).where(ResumeParsedData.resume_id == resume_id))
    parsed_data = result.scalars().first()
    assert parsed_data is not None
    assert parsed_data.skills == ["Python", "SQL"]
    
    # Verify Candidate Embedding row (to ensure Qdrant linking works)
    result_emb = await db_session.execute(select(CandidateEmbedding).where(CandidateEmbedding.candidate_id == cand_a_id))
    emb = result_emb.scalars().first()
    assert emb is not None
    assert emb.model_version == EMBEDDING_MODEL_NAME
    assert emb.qdrant_point_id is not None
    
    # Verify Qdrant was called
    mock_qdrant.upsert.assert_called_once()


@pytest.mark.asyncio
@patch("app.workers.tasks.resume_parser.AsyncSessionLocal")
async def test_resume_parser_failure_path(
    mock_session_local,
    db_session: AsyncSession,
    setup_candidate_data
):
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def get_mock_session():
        yield db_session
    mock_session_local.return_value = get_mock_session()
    
    from app.workers.tasks.resume_parser import async_parse_resume
    
    cand_a_id = setup_candidate_data["cand_a_id"]
    resume_id = uuid.uuid4()
    db_resume = Resume(
        id=resume_id,
        candidate_id=cand_a_id,
        file_url="nonexistent.pdf",
        parse_status=ParseStatus.PENDING
    )
    db_session.add(db_resume)
    await db_session.commit()
    
    # Run the parser async on a nonexistent file (will raise error in file handling)
    # The exception should be caught and status set to FAILED
    with pytest.raises(Exception):
        await async_parse_resume(str(resume_id))
    
    await db_session.refresh(db_resume)
    assert db_resume.parse_status == ParseStatus.FAILED


