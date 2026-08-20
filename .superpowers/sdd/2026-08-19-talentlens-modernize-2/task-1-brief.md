### Task 1: Auto-Fill from Backend & Remove Redundant Upload

**Files:**
- Modify: `D:\TalentLens\frontend\src\app\portal\jobs\page.tsx`
- Delete: `D:\TalentLens\frontend\src\components\JobBoard\AutoFillResume.tsx`
- Delete: `D:\TalentLens\frontend\tests\AutoFillResume.test.tsx`
- Modify: `D:\TalentLens\frontend\tests\page.test.tsx`

**Interfaces:**
- Consumes: `user` object passed to `ApplyModal` (which contains `.parsed_data`).
- Produces: A streamlined `ApplyModal` without file upload UI.

- [ ] **Step 1: Write the minimal implementation**

1. In `D:\TalentLens\frontend\src\app\portal\jobs\page.tsx`:
   - Inside `ApplyModal`, initialize state from `user?.parsed_data` if present.
   - For example: 
     `const [education, setEducation] = useState(user?.parsed_data?.education?.length > 0 ? user.parsed_data.education : [{ degree: "", institution: "", field_of_study: "" }]);`
     `const [experience, setExperience] = useState(user?.parsed_data?.experience?.length > 0 ? user.parsed_data.experience : [{ role: "", company: "", duration: "" }]);`
   - Remove `<AutoFillResume />` from the JSX.
   - Remove `file`, `resumeUploaded`, `fileInputRef`, and the fetch call to `/api/v1/candidate-portal/resume` inside `handleSubmit`.
   - Remove the `resume` check from `missingFields`.
2. Delete `D:\TalentLens\frontend\src\components\JobBoard\AutoFillResume.tsx`.
3. Delete `D:\TalentLens\frontend\tests\AutoFillResume.test.tsx`.
4. Fix any broken imports or tests in `page.test.tsx`.

- [ ] **Step 2: Commit**

```bash
git rm frontend/src/components/JobBoard/AutoFillResume.tsx
git rm frontend/tests/AutoFillResume.test.tsx
git add frontend/src/app/portal/jobs/page.tsx frontend/tests/page.test.tsx
git commit -m "refactor(portal): prefill apply form from db and remove redundant upload"
```
