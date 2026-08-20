### Task 1: Backend Database & Schema Evolution

**Files:**
- Modify: `D:\TalentLens\backend\app\models\recruitment.py`
- Modify: `D:\TalentLens\backend\app\schemas\recruitment.py`

**Interfaces:**
- Add to `Job`:
  - `salary_range` (String, nullable=True)
  - `company_description` (String, nullable=True)
  - `key_responsibilities` (JSONType, default=list, nullable=True)
  - `expectations` (JSONType, default=list, nullable=True)
  - `benefits` (JSONType, default=list, nullable=True)
- Update `JobRead` and `JobCreate` schemas to match (using `Optional[str]` and `Optional[List[str]]`).
- Generate and apply Alembic migration (`cd backend && alembic revision --autogenerate -m "add indeed style job fields"`, then `alembic upgrade head`).

- [ ] **Step 1: Write the minimal implementation**
Modify `Job` in `recruitment.py`.
Modify `JobRead` and `JobCreate` in `schemas/recruitment.py`.

- [ ] **Step 2: Generate Migration**
Run: `cd D:\TalentLens\backend && alembic revision --autogenerate -m "add indeed style job fields"`
Then run: `alembic upgrade head`

- [ ] **Step 3: Commit**
`git add backend/app/models/recruitment.py backend/app/schemas/recruitment.py backend/alembic/versions/`
`git commit -m "feat(backend): add detailed job fields and migration"`
