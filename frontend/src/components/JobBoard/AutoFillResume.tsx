"use client";

import React, { useState } from 'react';

export interface AutoFillResumeProps {
  onExtractedData: (data: any) => void;
  onFileSelected: (file: File) => void;
}

export function AutoFillResume({ onExtractedData, onFileSelected }: AutoFillResumeProps) {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    onFileSelected(file);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch("/api/v1/candidate-portal/resume", {
        method: "POST",
        headers,
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
        <p className="text-sm text-indigo-600 mb-4">We&apos;ll extract your experience and education automatically.</p>
        <div className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center justify-center font-medium">
          {loading ? "Analyzing..." : "Upload Resume"}
        </div>
      </label>
    </div>
  );
}
