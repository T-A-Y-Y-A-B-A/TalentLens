"use client";

import { Sparkles, MapPin, Building, Clock, Briefcase } from "lucide-react";
import { MatchGateBar } from "@/components/ui/match-gate-bar";

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
          ? "border-primary bg-[var(--signal-light)] shadow-sm shadow-primary/10"
          : "border-border bg-card hover:-translate-y-1 hover:border-primary/30 hover:shadow-md"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">{job.title}</h3>
          <p className="text-sm text-muted-foreground">{job.org_name}</p>
        </div>
        
        <div className="flex flex-col gap-2 shrink-0 ml-4 items-end w-32">
          {job.composite_score !== null && (
            <MatchGateBar overallScore={Math.round(job.composite_score)} gateThreshold={75} />
          )}
          
          <div className="flex flex-col gap-1 items-end">
            {job.flags && job.flags.map(flag => {
              const label = flag === 'low_relevant_experience' ? 'Low Relevant Experience' :
                            flag === 'title_mismatch' ? 'Title Mismatch' :
                            flag === 'incomplete_jd_data' ? 'Incomplete JD Data' :
                            flag.replace(/_/g, ' ');
              return (
                <div key={flag} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] uppercase font-bold tracking-wide bg-[var(--gate)]/10 text-[var(--gate)] border border-[var(--gate)]/20">
                  {label}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
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
