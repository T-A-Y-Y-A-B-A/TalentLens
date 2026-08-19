"use client";

import React from 'react';
import { DollarSign, Building2, MapPin, Briefcase } from 'lucide-react';

export interface SplitLayoutJob {
  id: string;
  title: string;
  description: string;
  org_id?: string;
  salary_range?: string | null;
  company_description?: string | null;
  key_responsibilities?: string[] | null;
  expectations?: string[] | null;
  benefits?: string[] | null;
  location?: string | null;
  work_type?: string | null;
  organization_name?: string | null;
  department?: { name: string } | null;
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
  const getResponsibilities = (job: SplitLayoutJob) => {
    if (Array.isArray(job.key_responsibilities)) return job.key_responsibilities;
    if (typeof job.key_responsibilities === 'string') {
      return (job.key_responsibilities as string).split('\n').map(s => s.trim()).filter(Boolean);
    }
    return [];
  };

  const getExpectations = (job: SplitLayoutJob) => {
    if (Array.isArray(job.expectations)) return job.expectations;
    if (typeof job.expectations === 'string') {
      return (job.expectations as string).split('\n').map(s => s.trim()).filter(Boolean);
    }
    return [];
  };

  const getBenefits = (job: SplitLayoutJob) => {
    if (Array.isArray(job.benefits)) return job.benefits;
    if (typeof job.benefits === 'string') {
      return (job.benefits as string).split('\n').map(s => s.trim()).filter(Boolean);
    }
    return [];
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 min-h-[70vh]">
      {/* Left List */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4 overflow-y-auto max-h-[80vh] pr-2">
        {jobs.map((job: SplitLayoutJob) => {
          const isSelected = selectedJob?.id === job.id;
          const isApplied = appliedJobs.has(job.id);
          return (
            <div 
              key={job.id} 
              onClick={() => onSelectJob(job)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected 
                  ? 'border-indigo-600 bg-indigo-50/40 shadow-sm ring-1 ring-indigo-600' 
                  : 'border-zinc-200 hover:border-indigo-300 bg-white hover:shadow-sm'
              }`}
            >
              <h3 className="font-bold text-zinc-900 line-clamp-1">{job.title}</h3>
              
              <div className="flex flex-wrap items-center gap-x-2 text-xs text-zinc-500 mt-1">
                {job.organization_name && <span>{job.organization_name}</span>}
                {job.organization_name && (job.location || job.work_type) && <span>•</span>}
                {job.location && <span>{job.location}</span>}
                {!job.location && job.work_type && <span className="capitalize">{job.work_type.toLowerCase()}</span>}
              </div>

              {job.salary_range && (
                <div className="mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {job.salary_range}
                  </span>
                </div>
              )}

              <p className="text-sm text-zinc-600 line-clamp-2 mt-2 leading-snug">{job.description}</p>

              {isApplied && (
                <div className="mt-2.5">
                  <span className="inline-flex items-center text-xs font-semibold text-indigo-600">
                    Applied
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Right Detail */}
      <div className="w-full lg:w-2/3 bg-white border border-zinc-200 rounded-xl p-6 sm:p-8 overflow-y-auto max-h-[80vh] sticky top-4">
        {!selectedJob ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-zinc-400 text-center p-8">
            <Briefcase className="w-12 h-12 stroke-[1.5] text-zinc-300 mb-3" />
            <p className="font-medium text-zinc-500">Select a job to view details</p>
            <p className="text-xs text-zinc-400 mt-1">Choose a position from the left to view requirements and apply.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Detail Header */}
            <div className="border-b border-zinc-100 pb-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-2">
                  <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 tracking-tight">{selectedJob.title}</h1>
                  
                  <div className="flex flex-wrap items-center gap-3 text-sm text-zinc-600">
                    {selectedJob.organization_name && (
                      <span className="flex items-center gap-1.5 font-medium text-zinc-800">
                        <Building2 className="w-4 h-4 text-zinc-500" />
                        {selectedJob.organization_name}
                      </span>
                    )}
                    {selectedJob.department?.name && (
                      <span className="text-zinc-500">
                        ({selectedJob.department.name})
                      </span>
                    )}
                    {selectedJob.location && (
                      <span className="flex items-center gap-1.5 text-zinc-600">
                        <MapPin className="w-4 h-4 text-zinc-400" />
                        {selectedJob.location}
                      </span>
                    )}
                    {selectedJob.work_type && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-700 capitalize">
                        {selectedJob.work_type.toLowerCase()}
                      </span>
                    )}
                  </div>

                  {/* Prominent Salary Badge */}
                  {selectedJob.salary_range && (
                    <div className="pt-1">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm font-semibold">
                        <DollarSign className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>{selectedJob.salary_range}</span>
                      </span>
                    </div>
                  )}
                </div>

                {/* Apply Button */}
                <button 
                  onClick={() => onApply(selectedJob)} 
                  disabled={appliedJobs.has(selectedJob.id)}
                  className={`px-6 py-2.5 rounded-lg font-medium transition shrink-0 ${
                    appliedJobs.has(selectedJob.id) 
                      ? "bg-zinc-100 text-zinc-400 cursor-not-allowed border border-zinc-200" 
                      : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm hover:shadow"
                  }`}
                >
                  {appliedJobs.has(selectedJob.id) ? "Already Applied" : "Apply Now"}
                </button>
              </div>
            </div>

            {/* Sections */}
            <div className="space-y-6">
              {/* About the Company */}
              {selectedJob.company_description && (
                <div className="space-y-2">
                  <h2 className="text-lg font-bold text-zinc-900">About the Company</h2>
                  <div className="prose prose-zinc max-w-none text-zinc-700">
                    <p className="whitespace-pre-wrap leading-relaxed">{selectedJob.company_description}</p>
                  </div>
                </div>
              )}

              {/* Job Description */}
              <div className="space-y-2">
                <h2 className="text-lg font-bold text-zinc-900">Job Description</h2>
                <div className="prose prose-zinc max-w-none text-zinc-700">
                  <p className="whitespace-pre-wrap leading-relaxed">{selectedJob.description}</p>
                </div>
              </div>

              {/* Key Responsibilities */}
              {getResponsibilities(selectedJob).length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-bold text-zinc-900">Key Responsibilities</h2>
                  <div className="prose prose-zinc max-w-none">
                    <ul className="list-disc pl-5 space-y-1.5 text-zinc-700 text-sm">
                      {getResponsibilities(selectedJob).map((resp: string, idx: number) => (
                        <li key={idx} className="leading-relaxed">{resp}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Expectations */}
              {getExpectations(selectedJob).length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-bold text-zinc-900">Expectations</h2>
                  <div className="prose prose-zinc max-w-none">
                    <ul className="list-disc pl-5 space-y-1.5 text-zinc-700 text-sm">
                      {getExpectations(selectedJob).map((exp: string, idx: number) => (
                        <li key={idx} className="leading-relaxed">{exp}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Benefits */}
              {getBenefits(selectedJob).length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-bold text-zinc-900">Benefits</h2>
                  <div className="prose prose-zinc max-w-none">
                    <ul className="list-disc pl-5 space-y-1.5 text-zinc-700 text-sm">
                      {getBenefits(selectedJob).map((benefit: string, idx: number) => (
                        <li key={idx} className="leading-relaxed">{benefit}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

