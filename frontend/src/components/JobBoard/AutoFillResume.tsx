"use client";

import React, { useState } from 'react';
import { apiClient } from '@/lib/api/client';

export interface AutoFillResumeProps {
  onExtractedData: (data: any) => void;
  onFileSelected: (file: File) => void;
}

export function AutoFillResume({ onExtractedData, onFileSelected }: AutoFillResumeProps) {
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const processFile = async (file: File) => {
    onFileSelected(file);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const { data, error } = await apiClient.POST("/api/v1/candidate-portal/resume", {
        body: formData as any,
        bodySerializer: (body) => body,
      });

      if (!error && data) {
        // Assume backend returns parsed JSON from resume text
        if ((data as any).parsed) {
          onExtractedData((data as any).parsed);
        }
      }
    } catch (err) {
      console.error("Failed to parse resume:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    await processFile(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await processFile(file);
    }
  };

  return (
    <div
      data-testid="autofill-dropzone"
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
        isDragging
          ? "border-indigo-600 bg-indigo-100/70"
          : "border-indigo-200 bg-indigo-50/50 hover:bg-indigo-50"
      }`}
    >
      <input
        type="file"
        id="resume-upload"
        className="hidden"
        accept=".pdf,.docx"
        onChange={handleUpload}
      />
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
