"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { JobCard, JobCardData } from "./JobCard";
import { FilterBar, JobBoardFilters } from "./FilterBar";
import { useAuth } from "@/components/providers/AuthProvider";

const DEFAULT_FILTERS: JobBoardFilters = {
  search: "",
  work_type: null,
  location: "",
  salary_min: null,
  sort_by_match: false,
};

function JobBoardContent() {
  const { user } = useAuth();
  const hasResume = !!((user as any)?.parsed_data?.education || (user as any)?.parsed_data?.experience);

  const [jobs, setJobs] = useState<JobCardData[]>([]);
  const [filters, setFilters] = useState<JobBoardFilters>(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.work_type) params.set("work_type", filters.work_type);
    if (filters.location) params.set("location", filters.location);
    if (filters.salary_min) params.set("salary_min", String(filters.salary_min));
    if (filters.sort_by_match) params.set("sort_by_match", "true");
    if (filters.search) params.set("q", filters.search);

    const res = await fetch(`/api/jobs/board?${params.toString()}`);
    const data = await res.json();
    setJobs(data.jobs);
    setLoading(false);
  }, [filters]);

  useEffect(() => {
    const t = setTimeout(fetchJobs, 250); // debounce search/typing
    return () => clearTimeout(t);
  }, [fetchJobs]);

  const handleApply = async (jobId: string) => {
    if (hasResume) {
      await fetch(`/api/jobs/${jobId}/apply`, { method: "POST" });
      // TODO: toast "Applied" + optimistic UI update
    } else {
      // TODO: open resume upload modal, then apply
    }
  };

  const selected = jobs.find((j) => j.id === selectedId) ?? null;

  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Left: filterable list */}
      <div className="flex w-full max-w-md flex-col border-r border-zinc-200 bg-white lg:max-w-lg">
        <FilterBar
          filters={filters}
          onChange={setFilters}
          hasResume={hasResume}
          resultCount={jobs.length}
        />
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {loading && (
            <div className="py-12 text-center text-sm text-zinc-500">Loading roles...</div>
          )}
          {!loading && jobs.length === 0 && (
            <div className="py-12 text-center text-sm text-zinc-500">
              No roles match your filters yet — try widening your search.
            </div>
          )}
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              hasResume={hasResume}
              onApply={handleApply}
              onSelect={setSelectedId}
              isSelected={job.id === selectedId}
            />
          ))}
        </div>
      </div>

      {/* Right: detail pane */}
      <div className="hidden flex-1 overflow-y-auto p-8 bg-zinc-50 lg:block">
        {!selected ? (
          <div className="flex h-full items-center justify-center text-zinc-500">
            Select a role to see full details
          </div>
        ) : (
          <div className="mx-auto max-w-2xl bg-white p-8 rounded-xl shadow-sm border border-zinc-200">
            <h1 className="text-2xl font-bold text-zinc-900">{selected.title}</h1>
            <p className="mt-1 text-zinc-500">{selected.org_name}</p>
            {/* Full job description, missing_skills breakdown, apply CTA go here */}
          </div>
        )}
      </div>
    </div>
  );
}

export default function JobBoardPage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-64">Loading...</div>}>
      <JobBoardContent />
    </Suspense>
  );
}
