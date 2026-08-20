### Task 4: Candidate Portal - Indeed-Style UI Redesign

**Files:**
- Modify: `D:\TalentLens\frontend\src\components\JobBoard\SplitLayout.tsx`

**Interfaces:**
- Updates the right-hand side detail view for a selected job to display the new structured fields (salary_range, company_description, key_responsibilities, expectations, benefits).
- Keeps the existing mobile responsiveness and Tailwind v4 typography plugin configuration.

- [ ] **Step 1: Write the minimal implementation**
1. In `SplitLayout.tsx`, display the `salary_range` below the job title (using a nice badge or green text like Indeed).
2. Add a `company_description` section.
3. Add a "Key Responsibilities" section with bullet points mapping over `selectedJob.key_responsibilities` (if it exists and is an array).
4. Add "Expectations" and "Benefits" sections mapping over their respective arrays if they exist.
5. Use `@tailwindcss/typography` (`className="prose prose-zinc"`) to ensure the rendering is beautiful.
6. Make sure the left-hand job list cards show a snippet of the salary range as well, if available.

- [ ] **Step 2: Commit**
`git add frontend/src/components/JobBoard/SplitLayout.tsx`
`git commit -m "feat(frontend): redesign candidate job board with indeed style layouts"`
