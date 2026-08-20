"use client";

import { Sparkles, MapPin, Building, Clock, Briefcase } from "lucide-react";

export type JobCardData = {
  id: string;
  title: string;
  org_name: string;
  work_type: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  salary_period: string;
  composite_score: number | null;
  flags: string[] | null;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  posted_at: string;
  key_responsibilities?: string | null;
  expectations?: string | null;
  requirements?: any | null;
  benefits?: string | null;
  company_description?: string | null;
};

export function JobCard({
  job,
  hasResume,
  onApply,
  onSelect,
  isSelected,
}: {
  job: JobCardData;
  hasResume: boolean;
  onApply: (id: string) => void;
  onSelect: (id: string) => void;
  isSelected: boolean;
}) {
  return (
    <div
      onClick={() => onSelect(job.id)}
      className={`cursor-pointer rounded-xl border p-4 transition-all duration-300 ${
        isSelected
          ? "border-indigo-500 bg-indigo-50/50 shadow-sm shadow-indigo-500/10"
          : "border-zinc-200 bg-white hover:-translate-y-1 hover:border-zinc-300 hover:shadow-md"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-zinc-900">{job.title}</h3>
          <p className="text-sm text-zinc-500">{job.org_name}</p>
        </div>
        {job.composite_score !== null && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-400 border border-blue-500/20">
            <Sparkles className="h-3 w-3" /> {Math.round(job.composite_score)}% Match
          </div>
        )}
        {job.flags && job.flags.map(flag => (
          <div key={flag} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            {flag}
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-500">
        <span className="flex items-center gap-1">
          <MapPin className="h-3 w-3" /> {job.location || "Remote"}
        </span>
        <span className="flex items-center gap-1">
          <Briefcase className="h-3 w-3" /> {job.work_type}
        </span>
        {job.salary_min && job.salary_max && (
          <span className="flex items-center gap-1 text-emerald-600 font-medium">
            <span className="font-mono">$</span>
            {job.salary_min.toLocaleString()} - {job.salary_max.toLocaleString()} {job.currency}
          </span>
        )}
      </div>
    </div>
  );
}
