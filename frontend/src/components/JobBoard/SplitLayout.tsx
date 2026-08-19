"use client";

import React from 'react';

export interface SplitLayoutJob {
  id: string;
  title: string;
  description: string;
  org_id?: string;
  [key: string]: any;
}

export interface SplitLayoutProps {
  jobs: SplitLayoutJob[];
  selectedJob: SplitLayoutJob | null;
  onSelectJob: (job: SplitLayoutJob) => void;
  onApply: (job: SplitLayoutJob) => void;
  appliedJobs: Set<string>;
}

export function SplitLayout({ jobs, selectedJob, onSelectJob, onApply, appliedJobs }: SplitLayoutProps) {
  return (
    <div className="flex flex-col lg:flex-row gap-6 min-h-[70vh]">
      {/* Left List */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4 overflow-y-auto max-h-[80vh] pr-2">
        {jobs.map((job: SplitLayoutJob) => (
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
            <button 
              onClick={() => onApply(selectedJob)} 
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition"
            >
              {appliedJobs.has(selectedJob.id) ? "Already Applied" : "Apply Now"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
