import asyncio
from httpx import AsyncClient

async def main():
    async with AsyncClient(base_url='http://localhost:8000/api/v1', timeout=10.0) as client:
        # Login
        res = await client.post('/auth/login', json={'email': 'hr@digitalsofts.com', 'password': 'password123'})
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        token = res.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Get App
        res = await client.get('/applications', headers=headers)
        apps = res.json()
        app_id = apps[0]['id']

        # Get user
        res = await client.get('/auth/me', headers=headers)
        hr_id = res.json()['id']

        # Create
        payload = {
            'application_id': app_id,
            'interviewer_id': hr_id,
            'scheduled_at': '2026-08-10T10:00:00Z',
            'duration_minutes': 45,
            'meeting_link': 'https://meet.google.com/abc-defg-hij',
            'notes': 'Test interview from host'
        }
        res = await client.post('/interviews', json=payload, headers=headers)
        print("POST /interviews ->", res.status_code)
        print(res.json())

        # Update
        patch_payload = {'duration_minutes': 60}
        interview_id = res.json()['id']
        res = await client.patch(f'/interviews/{interview_id}', json=patch_payload, headers=headers)
        print("PATCH /interviews ->", res.status_code)
        
        # Delete
        res = await client.delete(f'/interviews/{interview_id}', headers=headers)
        print("DELETE /interviews ->", res.status_code)

asyncio.run(main())
