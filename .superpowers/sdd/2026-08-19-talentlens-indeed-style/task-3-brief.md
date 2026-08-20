### Task 3: HR Dashboard - AI Job Creation Form

**Files:**
- Modify: `D:\TalentLens\frontend\src\app\dashboard\jobs\page.tsx`
- Build/Run API: Ensure the OpenAPI schemas are updated (`cd D:\TalentLens\frontend && npm run generate:api`)

**Interfaces:**
- Add a new "Enhance with AI" section in the Job Creation dialog.
- Let the HR user type `roughNotes`. 
- Have an "Enhance with AI" button that calls `POST /api/v1/jobs/enhance` using `apiClient.POST`.
- On success, auto-fill `title`, `description`, `salary_range`, `company_description`, and store the JSON arrays (`key_responsibilities`, `expectations`, `benefits`) in state to be submitted.
- Update the job creation payload (to `POST /api/v1/jobs`) to include the new fields.

- [ ] **Step 1: Write the minimal implementation**
1. Run `cd D:\TalentLens\frontend && npm run generate:api` to fetch the new schemas.
2. In `frontend/src/app/dashboard/jobs/page.tsx`:
   - Add state variables for the new fields: `salaryRange`, `companyDescription`, `keyResponsibilities` (string or array of strings, maybe a multiline text area where they are joined by newlines for editing, or just keep them as raw state and let the user edit them via text area). Let's use `textarea` where they join with `\n`.
   - Add a `roughNotes` state and an `isEnhancing` loading state.
   - Add the Enhance with AI UI (a text area and button).
   - When the button is clicked, call `POST /api/v1/jobs/enhance`, and update all states based on the response.
   - Include `salary_range`, `company_description`, `key_responsibilities`, `expectations`, `benefits` in the submit payload to `POST /api/v1/jobs`.

- [ ] **Step 2: Commit**
`git add frontend/src/app/dashboard/jobs/page.tsx frontend/src/lib/api/schema.d.ts`
`git commit -m "feat(frontend): add AI job enhancement to HR dashboard"`
