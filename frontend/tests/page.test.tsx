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
