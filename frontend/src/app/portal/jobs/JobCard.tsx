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
  match_pct: number | null;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  posted_at: string;
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
          ? "border-indigo-500 bg-slate-900 shadow-md shadow-indigo-500/20"
          : "border-slate-800 bg-slate-900/50 hover:-translate-y-1 hover:border-slate-700 hover:shadow-lg"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-100">{job.title}</h3>
          <p className="text-sm text-slate-400">{job.org_name}</p>
        </div>
        {job.match_pct !== null && (
          <div className="flex items-center gap-1 rounded-full bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-400 border border-indigo-500/20">
            <Sparkles className="h-3 w-3" /> {Math.round(job.match_pct)}% Match
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <MapPin className="h-3 w-3" /> {job.location || "Remote"}
        </span>
        <span className="flex items-center gap-1">
          <Briefcase className="h-3 w-3" /> {job.work_type}
        </span>
        {job.salary_min && job.salary_max && (
          <span className="flex items-center gap-1 text-emerald-400/90 font-medium">
            <span className="font-mono">$</span>
            {job.salary_min.toLocaleString()} - {job.salary_max.toLocaleString()} {job.currency}
          </span>
        )}
      </div>
    </div>
  );
}
