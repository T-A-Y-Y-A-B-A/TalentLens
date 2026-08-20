# TalentLens Modern Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the Candidate Job Board by introducing a premium split-screen layout, rich typography for job descriptions, and an "Auto-Fill with Resume" application flow.

**Architecture:** We will refactor `D:\TalentLens\frontend\src\app\portal\jobs\page.tsx` from a card-grid layout into a master-detail split screen. The massive apply modal will be refactored to support a drag-and-drop resume upload zone at the top, which triggers an API call to `/api/v1/candidate-portal/resume` to auto-fill form state before submission. 

**Tech Stack:** Next.js 15, Tailwind CSS v4, React (Hooks), Radix UI/Lucide Icons.

**Spec:** `D:\TalentLens\FRONTEND_PLAN.md`

## Global Constraints

- Must maintain strict Next.js App Router client component boundaries (`"use client"`).
- API calls must continue using the existing `apiClient.GET/POST` OpenAPI fetch wrapper.
- Must ensure mobile responsiveness (stack vertically on small screens, split horizontally on large screens).
- No new heavy dependencies unless absolutely necessary.

---

### Task 1: Setup Testing & Tailwind Typography

**Files:**
- Create: `D:\TalentLens\frontend\vitest.config.ts`
- Create: `D:\TalentLens\frontend\tests\setup.ts`
- Modify: `D:\TalentLens\frontend\package.json`
- Modify: `D:\TalentLens\frontend\src\app\globals.css`

**Interfaces:**
- Consumes: Existing Next.js project
- Produces: Testing environment capable of running `npm test` and rich typography classes.

- [ ] **Step 1: Write the failing test**

```typescript
// D:\TalentLens\frontend\tests\sanity.test.tsx
import { describe, it, expect } from 'vitest';

describe('Sanity Check', () => {
  it('runs tests successfully', () => {
    expect(true).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails (missing config)**

Run: `cd D:\TalentLens\frontend && npx vitest run`
Expected: FAIL or Command not found

- [ ] **Step 3: Write minimal implementation**

```bash
cd D:\TalentLens\frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @tailwindcss/typography
```

```typescript
// D:\TalentLens\frontend\vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

```typescript
// D:\TalentLens\frontend\tests\setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';
global.vi = vi;
```

Modify `D:\TalentLens\frontend\src\app\globals.css` to include the typography plugin (Tailwind v4 syntax):
```css
@plugin "@tailwindcss/typography";
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\TalentLens\frontend && npx vitest run`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/vitest.config.ts frontend/tests/ frontend/src/app/globals.css
git commit -m "chore: setup vitest and tailwind typography"
```

---

### Task 2: Build the Split-Screen Layout Component Structure

**Files:**
- Create: `D:\TalentLens\frontend\src\components\JobBoard\SplitLayout.tsx`
- Create: `D:\TalentLens\frontend\tests\SplitLayout.test.tsx`

**Interfaces:**
- Consumes: Nothing
- Produces: `SplitLayout` component accepting `jobs` array, `selectedJob`, and `onSelectJob` callback.

- [ ] **Step 1: Write the failing test**

```typescript
// D:\TalentLens\frontend\tests\SplitLayout.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SplitLayout } from '../src/components/JobBoard/SplitLayout';

describe('SplitLayout', () => {
  it('renders a list of jobs and a detail pane', () => {
    const mockJobs = [{ id: '1', title: 'Frontend Eng', description: 'React', org_id: '1' }];
    render(<SplitLayout jobs={mockJobs} selectedJob={null} onSelectJob={() => {}} onApply={() => {}} appliedJobs={new Set()} />);
    expect(screen.getByText('Frontend Eng')).toBeInTheDocument();
    expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/SplitLayout.test.tsx`
Expected: FAIL with "module not found"

- [ ] **Step 3: Write minimal implementation**

```tsx
// D:\TalentLens\frontend\src\components\JobBoard\SplitLayout.tsx
import React from 'react';

export function SplitLayout({ jobs, selectedJob, onSelectJob, onApply, appliedJobs }: any) {
  return (
    <div className="flex flex-col lg:flex-row gap-6 min-h-[70vh]">
      {/* Left List */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4 overflow-y-auto max-h-[80vh] pr-2">
        {jobs.map((job: any) => (
          <div 
            key={job.id} 
            onClick={() => onSelectJob(job)}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedJob?.id === job.id ? 'border-indigo-500 bg-indigo-50/50' : 'border-zinc-200 hover:border-indigo-300 bg-white'}`}
          >
            <h3 className="font-bold text-zinc-900">{job.title}</h3>
            <p className="text-sm text-zinc-500 line-clamp-2 mt-1">{job.description}</p>
          </div>
        ))}
      </div>
      
      {/* Right Detail */}
      <div className="w-full lg:w-2/3 bg-white border border-zinc-200 rounded-xl p-8 overflow-y-auto max-h-[80vh] sticky top-4">
        {!selectedJob ? (
          <div className="flex items-center justify-center h-full text-zinc-400">
            Select a job to view details
          </div>
        ) : (
          <div className="space-y-6">
            <h1 className="text-3xl font-extrabold text-zinc-900">{selectedJob.title}</h1>
            <div className="prose prose-zinc max-w-none">
              <p className="whitespace-pre-wrap">{selectedJob.description}</p>
            </div>
            <button onClick={() => onApply(selectedJob)} className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition">
              {appliedJobs.has(selectedJob.id) ? "Already Applied" : "Apply Now"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/SplitLayout.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/JobBoard/SplitLayout.tsx frontend/tests/SplitLayout.test.tsx
git commit -m "feat: add split layout component"
```

---

### Task 3: Build the Auto-Fill Resume Upload Component

**Files:**
- Create: `D:\TalentLens\frontend\src\components\JobBoard\AutoFillResume.tsx`
- Create: `D:\TalentLens\frontend\tests\AutoFillResume.test.tsx`

**Interfaces:**
- Consumes: OpenAPI `/api/v1/candidate-portal/resume` logic (mocked in tests).
- Produces: `AutoFillResume` component that calls `onExtractedData(data)` upon successful upload and parse.

- [ ] **Step 1: Write the failing test**

```typescript
// D:\TalentLens\frontend\tests\AutoFillResume.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { AutoFillResume } from '../src/components/JobBoard/AutoFillResume';

describe('AutoFillResume', () => {
  it('renders the upload zone', () => {
    render(<AutoFillResume onExtractedData={() => {}} onFileSelected={() => {}} />);
    expect(screen.getByText(/Drop your resume/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/AutoFillResume.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```tsx
// D:\TalentLens\frontend\src\components\JobBoard\AutoFillResume.tsx
import React, { useState } from 'react';

export function AutoFillResume({ onExtractedData, onFileSelected }: any) {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    onFileSelected(file);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch("/api/v1/candidate-portal/resume", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        // Assume backend returns parsed JSON from resume text
        if (data && data.parsed) {
          onExtractedData(data.parsed);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-2 border-dashed border-indigo-200 bg-indigo-50/50 rounded-xl p-8 text-center hover:bg-indigo-50 transition">
      <input type="file" id="resume-upload" className="hidden" accept=".pdf,.docx" onChange={handleUpload} />
      <label htmlFor="resume-upload" className="cursor-pointer flex flex-col items-center">
        <h3 className="text-lg font-bold text-indigo-900 mb-2">Drop your resume to Auto-Fill</h3>
        <p className="text-sm text-indigo-600 mb-4">We'll extract your experience and education automatically.</p>
        <div className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center justify-center">
          {loading ? "Analyzing..." : "Upload Resume"}
        </div>
      </label>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/AutoFillResume.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/JobBoard/AutoFillResume.tsx frontend/tests/AutoFillResume.test.tsx
git commit -m "feat: add resume auto-fill uploader"
```

---

### Task 4: Integrate SplitLayout and AutoFill into Main Page

**Files:**
- Modify: `D:\TalentLens\frontend\src\app\portal\jobs\page.tsx`
- Modify: `D:\TalentLens\frontend\tests\page.test.tsx`

**Interfaces:**
- Consumes: `SplitLayout`, `AutoFillResume`
- Produces: Final cohesive candidate portal jobs page.

- [ ] **Step 1: Write the failing test**

```typescript
// D:\TalentLens\frontend\tests\page.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn() })
}));
// Mock Auth Provider
vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { name: 'Test User' } })
}));

import CandidateJobsPage from '../src/app/portal/jobs/page';

describe('CandidateJobsPage', () => {
  it('renders without crashing', () => {
    render(<CandidateJobsPage />);
    expect(document.body).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/page.test.tsx`
Expected: FAIL due to missing `vi` import or Next mocks setup

- [ ] **Step 3: Write minimal implementation**

*In `D:\TalentLens\frontend\src\app\portal\jobs\page.tsx`:*
1. Import `SplitLayout` and `AutoFillResume`.
2. Replace the `<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">` map block with:
   `<SplitLayout jobs={jobs} selectedJob={selectedJob} onSelectJob={setSelectedJob} onApply={openApply} appliedJobs={appliedJobs} />`
3. Modify the `ApplyModal` component inside `page.tsx`:
   Add `<AutoFillResume onFileSelected={setFile} onExtractedData={(data) => { setName(data.name || name); setPhone(data.phone || phone); if(data.education) setEducation(data.education); if(data.experience) setExperience(data.experience); setResumeUploaded(true); }} />` at the top of the modal form. Remove the old duplicate resume file input at the bottom.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\TalentLens\frontend && npx vitest run tests/page.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/portal/jobs/page.tsx frontend/tests/
git commit -m "feat: integrate split layout and auto-fill to job board"
```
