### Task 2: AI Enhancer API Endpoint

**Files:**
- Modify/Create: `D:\TalentLens\backend\app\api\v1\jobs.py` (or existing job routes)
- Modify: `D:\TalentLens\backend\app\schemas\recruitment.py` (Add Request/Response schemas for AI enhancement)

**Interfaces:**
- Use existing OpenAI client from the backend. (Usually `from openai import AsyncOpenAI`).
- Expose `POST /api/v1/jobs/enhance` accepting:
```python
class JobEnhanceRequest(BaseModel):
    rough_notes: str

class JobEnhanceResponse(BaseModel):
    title: str
    description: str
    salary_range: Optional[str]
    company_description: Optional[str]
    key_responsibilities: Optional[List[str]]
    expectations: Optional[List[str]]
    benefits: Optional[List[str]]
```

- [ ] **Step 1: Write the minimal implementation**
1. Add `JobEnhanceRequest` and `JobEnhanceResponse` to `backend/app/schemas/recruitment.py`.
2. Add `@router.post("/enhance", response_model=JobEnhanceResponse)` to `backend/app/api/v1/jobs.py` (ensure you check if `router` exists or if it's imported in `main.py`).
   Wait, if `jobs.py` doesn't exist, create it and register it in `backend/app/api/v1/api.py`. Wait, earlier I saw `jobs.py` in `grep_search`. Yes, it exists.
3. In the endpoint, call `client = AsyncOpenAI()` (or however it's configured in `app.core.config`). Send a prompt asking the AI to parse `rough_notes` and return a strict JSON matching `JobEnhanceResponse`. Use `response_format={ "type": "json_object" }` or structured outputs.
4. Return the parsed JSON.

- [ ] **Step 2: Commit**
`git add backend/app/api/v1/jobs.py backend/app/schemas/recruitment.py`
`git commit -m "feat(backend): add job enhancement ai endpoint"`
