import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AutoFillResume } from '../src/components/JobBoard/AutoFillResume';
import { apiClient } from '../src/lib/api/client';

vi.mock('../src/lib/api/client', () => ({
  apiClient: {
    POST: vi.fn(),
  },
}));

describe('AutoFillResume', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the upload zone', () => {
    render(<AutoFillResume onExtractedData={() => {}} onFileSelected={() => {}} />);
    expect(screen.getByText(/Drop your resume/i)).toBeInTheDocument();
  });

  it('handles file upload via input change and calls callbacks', async () => {
    const handleExtracted = vi.fn();
    const handleFileSelected = vi.fn();

    const mockParsed = {
      name: 'Jane Doe',
      email: 'jane@example.com',
      experience: '5 years'
    };

    vi.mocked(apiClient.POST).mockResolvedValue({
      data: { parsed: mockParsed } as any,
      error: null,
      response: new Response(),
    });

    render(<AutoFillResume onExtractedData={handleExtracted} onFileSelected={handleFileSelected} />);

    const file = new File(['dummy resume content'], 'resume.pdf', { type: 'application/pdf' });
    const input = document.getElementById('resume-upload') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    expect(handleFileSelected).toHaveBeenCalledWith(file);
    await waitFor(() => {
      expect(apiClient.POST).toHaveBeenCalledWith(
        '/api/v1/candidate-portal/resume',
        expect.objectContaining({
          body: expect.any(FormData),
        })
      );
      expect(handleExtracted).toHaveBeenCalledWith(mockParsed);
    });
  });

  it('handles drag-and-drop events and file drop', async () => {
    const handleExtracted = vi.fn();
    const handleFileSelected = vi.fn();

    const mockParsed = {
      name: 'John Smith',
      email: 'john@example.com',
      experience: '3 years'
    };

    vi.mocked(apiClient.POST).mockResolvedValue({
      data: { parsed: mockParsed } as any,
      error: null,
      response: new Response(),
    });

    render(<AutoFillResume onExtractedData={handleExtracted} onFileSelected={handleFileSelected} />);

    const dropzone = screen.getByTestId('autofill-dropzone');
    const file = new File(['resume content'], 'my-resume.pdf', { type: 'application/pdf' });

    // Drag enter and drag over
    fireEvent.dragEnter(dropzone);
    fireEvent.dragOver(dropzone);

    // Drop file
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file],
      },
    });

    expect(handleFileSelected).toHaveBeenCalledWith(file);
    await waitFor(() => {
      expect(apiClient.POST).toHaveBeenCalledWith(
        '/api/v1/candidate-portal/resume',
        expect.objectContaining({
          body: expect.any(FormData),
        })
      );
      expect(handleExtracted).toHaveBeenCalledWith(mockParsed);
    });
  });

  it('updates drag state on dragLeave', () => {
    render(<AutoFillResume onExtractedData={() => {}} onFileSelected={() => {}} />);
    const dropzone = screen.getByTestId('autofill-dropzone');

    fireEvent.dragEnter(dropzone);
    expect(dropzone.className).toContain('border-indigo-600');

    fireEvent.dragLeave(dropzone);
    expect(dropzone.className).toContain('border-indigo-200');
  });
});
