import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid
import json
from app.models.identity import Organization
from app.models.recruitment import Job, JobStatus
from app.models.candidate import Candidate
from app.core.security import create_access_token

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@postgres:5432/talentlens')
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        # Create 2 Orgs
        org1_id = uuid.uuid4()
        org2_id = uuid.uuid4()
        db.add(Organization(id=org1_id, name='Org 1', slug=str(uuid.uuid4())))
        db.add(Organization(id=org2_id, name='Org 2', slug=str(uuid.uuid4())))
        
        # Create 2 Jobs
        job1_id = uuid.uuid4()
        job2_id = uuid.uuid4()
        db.add(Job(id=job1_id, org_id=org1_id, title='Job Org 1', description='Desc', status=JobStatus.OPEN))
        db.add(Job(id=job2_id, org_id=org2_id, title='Job Org 2', description='Desc', status=JobStatus.OPEN))
        
        # Create Candidate
        cand_id = uuid.uuid4()
        db.add(Candidate(id=cand_id, name='Test Cand', email=f'test{cand_id}@example.com', source='portal'))
        await db.commit()
        
        token = create_access_token(subject=cand_id, additional_claims={'role': 'candidate'})
        
    print(f'Token generated')
    
    headers = {'Authorization': f'Bearer {token}'}
    async with httpx.AsyncClient(base_url='http://localhost:8000', timeout=None) as client:
        # Test GET /jobs
        print('--- GET /jobs ---')
        r = await client.get('/api/v1/candidate-portal/jobs', headers=headers)
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            jobs = r.json()
            print(f'Jobs returned: {len(jobs)}')
            for j in jobs:
                print(f"- {j['title']} (Org: {j['org_id']})")
        else:
            print(f'Body: {r.text}')
            
        # Test Duplicate Application
        print('\n--- Apply to Job 1 ---')
        r_apply1 = await client.post('/api/v1/candidate-portal/apply', headers=headers, json={'job_id': str(job1_id)})
        print(f'First apply status: {r_apply1.status_code}')
        
        print('\n--- Duplicate Apply to Job 1 ---')
        r_apply2 = await client.post('/api/v1/candidate-portal/apply', headers=headers, json={'job_id': str(job1_id)})
        print(f'Second apply status: {r_apply2.status_code}')
        print(f'Second apply body: {r_apply2.text}')
        
        # Test 5.1MB Upload (which might get caught by headers in httpx, so we also bypass header explicitly)
        print('\n--- 5.1MB Upload ---')
        import io
        big_file = io.BytesIO(b'0' * int(5.1 * 1024 * 1024))
        
        # 1. Normal upload with httpx (sends content-length)
        files = {'file': ('resume.pdf', big_file, 'application/pdf')}
        r_upload1 = await client.post('/api/v1/candidate-portal/resume', headers=headers, files=files)
        print(f'Normal 5.1MB upload status: {r_upload1.status_code}')
        print(f'Normal 5.1MB upload body: {r_upload1.text}')
        
        # 2. Upload without content-length header (spoofing) to prove chunk reading works
        print('\n--- Spoofed Content-Length Large Upload ---')
        big_file.seek(0)
        # We can use httpx stream to avoid it setting the content-length
        async def generate_chunks():
            # Send exactly 5.1MB
            yield b'0' * int(5.1 * 1024 * 1024)
        
        # Multipart form data manually
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body_start = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="resume.pdf"\r\n'
            f'Content-Type: application/pdf\r\n\r\n'
        ).encode('utf-8')
        body_end = f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        async def spoof_stream():
            yield body_start
            yield b'0' * int(5.1 * 1024 * 1024)
            yield body_end
            
        spoofed_headers = headers.copy()
        spoofed_headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        if 'Content-Length' in spoofed_headers:
            del spoofed_headers['Content-Length']
            
        r_upload2 = await client.post('/api/v1/candidate-portal/resume', headers=spoofed_headers, content=spoof_stream())
        print(f'Spoofed/Large upload status: {r_upload2.status_code}')
        print(f'Spoofed/Large upload body: {r_upload2.text}')

asyncio.run(main())
