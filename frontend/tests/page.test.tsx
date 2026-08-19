import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

// Mock apiClient
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    GET: vi.fn().mockResolvedValue({ data: [], error: null }),
    POST: vi.fn().mockResolvedValue({ data: {}, error: null }),
    use: vi.fn(),
  }
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn() })
}));

// Mock Auth Provider
vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { name: 'Test User', email: 'test@example.com' } })
}));

import CandidateJobsPage from '../src/app/portal/jobs/page';

describe('CandidateJobsPage', () => {
  it('renders without crashing', async () => {
    render(<CandidateJobsPage />);
    await waitFor(() => {
      expect(document.body).toBeDefined();
    });
  });
});
