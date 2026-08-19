import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AutoFillResume } from '../src/components/JobBoard/AutoFillResume';

describe('AutoFillResume', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the upload zone', () => {
    render(<AutoFillResume onExtractedData={() => {}} onFileSelected={() => {}} />);
    expect(screen.getByText(/Drop your resume/i)).toBeInTheDocument();
  });

  it('handles file upload and calls callbacks', async () => {
    const handleExtracted = vi.fn();
    const handleFileSelected = vi.fn();

    const mockParsed = {
      name: 'Jane Doe',
      email: 'jane@example.com',
      experience: '5 years'
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ parsed: mockParsed })
    });

    render(<AutoFillResume onExtractedData={handleExtracted} onFileSelected={handleFileSelected} />);

    const file = new File(['dummy resume content'], 'resume.pdf', { type: 'application/pdf' });
    const input = document.getElementById('resume-upload') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    expect(handleFileSelected).toHaveBeenCalledWith(file);
    await waitFor(() => {
      expect(handleExtracted).toHaveBeenCalledWith(mockParsed);
    });
  });
});
