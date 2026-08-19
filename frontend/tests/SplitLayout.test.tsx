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

  it('renders Indeed-style structured fields (salary, company desc, responsibilities, expectations, benefits)', () => {
    const structuredJob = {
      id: '3',
      title: 'Full Stack Engineer',
      description: 'Join our dynamic team building next-gen web apps.',
      salary_range: '$120,000 - $150,000 / year',
      company_description: 'Acme Corp is an innovator in AI tech.',
      key_responsibilities: ['Build React frontends', 'Design FastAPI backends'],
      expectations: ['5+ years experience', 'Fast learner'],
      benefits: ['Health insurance', '401(k) matching', 'Remote work'],
      organization_name: 'Acme Corp',
      location: 'San Francisco, CA',
      work_type: 'HYBRID'
    };

    render(
      <SplitLayout 
        jobs={[structuredJob]} 
        selectedJob={structuredJob} 
        onSelectJob={() => {}} 
        onApply={() => {}} 
        appliedJobs={new Set()} 
      />
    );

    // Check salary badge in both list and detail view
    const salaryBadges = screen.getAllByText('$120,000 - $150,000 / year');
    expect(salaryBadges.length).toBeGreaterThanOrEqual(2);

    // Check Company Description
    expect(screen.getByText('About the Company')).toBeInTheDocument();
    expect(screen.getByText('Acme Corp is an innovator in AI tech.')).toBeInTheDocument();

    // Check Key Responsibilities
    expect(screen.getByText('Key Responsibilities')).toBeInTheDocument();
    expect(screen.getByText('Build React frontends')).toBeInTheDocument();
    expect(screen.getByText('Design FastAPI backends')).toBeInTheDocument();

    // Check Expectations
    expect(screen.getByText('Expectations')).toBeInTheDocument();
    expect(screen.getByText('5+ years experience')).toBeInTheDocument();
    expect(screen.getByText('Fast learner')).toBeInTheDocument();

    // Check Benefits
    expect(screen.getByText('Benefits')).toBeInTheDocument();
    expect(screen.getByText('Health insurance')).toBeInTheDocument();
    expect(screen.getByText('401(k) matching')).toBeInTheDocument();
    expect(screen.getByText('Remote work')).toBeInTheDocument();
  });
});
