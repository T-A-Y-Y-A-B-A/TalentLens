import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SplitLayout } from '../src/components/JobBoard/SplitLayout';

describe('SplitLayout', () => {
  const mockJobs = [
    { id: '1', title: 'Frontend Eng', description: 'React position', org_id: '1' },
    { id: '2', title: 'Backend Eng', description: 'Python position', org_id: '1' }
  ];

  it('renders a list of jobs and a detail pane', () => {
    render(
      <SplitLayout 
        jobs={mockJobs} 
        selectedJob={null} 
        onSelectJob={() => {}} 
        onApply={() => {}} 
        appliedJobs={new Set()} 
      />
    );
    expect(screen.getByText('Frontend Eng')).toBeInTheDocument();
    expect(screen.getByText('Backend Eng')).toBeInTheDocument();
    expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
  });

  it('renders job details and allows selection and application', () => {
    const handleSelect = vi.fn();
    const handleApply = vi.fn();

    const { rerender } = render(
      <SplitLayout 
        jobs={mockJobs} 
        selectedJob={null} 
        onSelectJob={handleSelect} 
        onApply={handleApply} 
        appliedJobs={new Set()} 
      />
    );

    // Click job card to select
    fireEvent.click(screen.getByText('Frontend Eng'));
    expect(handleSelect).toHaveBeenCalledWith(mockJobs[0]);

    // Rerender with selectedJob
    rerender(
      <SplitLayout 
        jobs={mockJobs} 
        selectedJob={mockJobs[0]} 
        onSelectJob={handleSelect} 
        onApply={handleApply} 
        appliedJobs={new Set()} 
      />
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Frontend Eng' })).toBeInTheDocument();
    expect(screen.getAllByText('React position').length).toBeGreaterThanOrEqual(1);

    const applyButton = screen.getByRole('button', { name: 'Apply Now' });
    fireEvent.click(applyButton);
    expect(handleApply).toHaveBeenCalledWith(mockJobs[0]);
  });

  it('shows Already Applied when job is in appliedJobs set', () => {
    render(
      <SplitLayout 
        jobs={mockJobs} 
        selectedJob={mockJobs[0]} 
        onSelectJob={() => {}} 
        onApply={() => {}} 
        appliedJobs={new Set(['1'])} 
      />
    );

    expect(screen.getByRole('button', { name: 'Already Applied' })).toBeInTheDocument();
  });
});
