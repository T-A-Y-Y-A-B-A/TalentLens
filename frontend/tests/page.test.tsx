import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CandidateJobsPage from '../src/app/portal/jobs/page';
import { apiClient } from '@/lib/api/client';

// Mock apiClient
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    GET: vi.fn(),
    POST: vi.fn(),
    use: vi.fn(),
  }
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn() })
}));

const mockUser = {
  name: 'Jane Doe',
  email: 'jane@example.com',
  parsed_data: {
    name: 'Jane Doe',
    phone: '+1 555-987-6543',
    education: [{ degree: 'M.S. Computer Science', institution: 'Stanford University', field_of_study: 'AI' }],
    experience: [{ role: 'Senior Developer', company: 'Acme Corp', duration: '2021 - 2024' }],
    certifications: [{ name: 'AWS Certified Solutions Architect', issuing_body: 'Amazon Web Services' }]
  }
};

// Mock Auth Provider
vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => ({ user: mockUser })
}));

describe('CandidateJobsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', async () => {
    vi.mocked(apiClient.GET).mockImplementation(async (url: string) => {
      if (url === '/api/v1/candidate-portal/jobs') {
        return { data: { jobs: [] } as any, error: null, response: new Response() };
      }
      if (url === '/api/v1/candidate-portal/applications') {
        return { data: [] as any, error: null, response: new Response() };
      }
      return { data: null, error: null, response: new Response() };
    });

    render(<CandidateJobsPage />);
    await waitFor(() => {
      expect(document.body).toBeDefined();
    });
  });

  it('opens apply modal with prefilled data from user parsed_data and submits application without file upload', async () => {
    const mockJobs = [
      {
        id: 'job-123',
        title: 'Full Stack Engineer',
        description: 'Building modern apps',
        org_id: 'org-1',
        created_at: '2026-01-01',
      }
    ];

    vi.mocked(apiClient.GET).mockImplementation(async (url: string) => {
      if (url === '/api/v1/candidate-portal/jobs') {
        return { data: { jobs: mockJobs } as any, error: null, response: new Response() };
      }
      if (url === '/api/v1/candidate-portal/applications') {
        return { data: [] as any, error: null, response: new Response() };
      }
      return { data: null, error: null, response: new Response() };
    });

    vi.mocked(apiClient.POST).mockResolvedValue({
      data: { success: true } as any,
      error: null,
      response: new Response(),
    });

    render(<CandidateJobsPage />);

    // Wait for job to load
    await waitFor(() => {
      expect(screen.getByText('Full Stack Engineer')).toBeInTheDocument();
    });

    // Click job card to select it
    fireEvent.click(screen.getByText('Full Stack Engineer'));

    // Wait for detail pane to show Apply Now button and click it
    const applyButton = await screen.findByRole('button', { name: 'Apply Now' });
    fireEvent.click(applyButton);

    // Check that modal opened with pre-filled fields
    await waitFor(() => {
      expect(screen.getByText('Apply for Full Stack Engineer')).toBeInTheDocument();
    });

    // Check autofilled fields
    expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+1 555-987-6543')).toBeInTheDocument();
    expect(screen.getByDisplayValue('M.S. Computer Science')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Stanford University')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Senior Developer')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Acme Corp')).toBeInTheDocument();

    // Verify AutoFill / upload dropzone is NOT present
    expect(screen.queryByText(/Drop your resume to Auto-Fill/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId('autofill-dropzone')).not.toBeInTheDocument();

    // Submit the form
    const submitBtn = screen.getByRole('button', { name: /Submit Application/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.POST).toHaveBeenCalledWith(
        '/api/v1/candidate-portal/apply',
        expect.objectContaining({
          body: {
            job_id: 'job-123',
            name: 'Jane Doe',
            phone: '+1 555-987-6543',
            education: [{ degree: 'M.S. Computer Science', institution: 'Stanford University', field_of_study: 'AI' }],
            work_experience: [{ role: 'Senior Developer', company: 'Acme Corp', duration: '2021 - 2024' }],
            certifications: [{ name: 'AWS Certified Solutions Architect', issuing_body: 'Amazon Web Services' }]
          }
        })
      );
    });
  });
});
