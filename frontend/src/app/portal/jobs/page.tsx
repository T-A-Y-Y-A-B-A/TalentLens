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
    params.set("limit", "100");

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/jobs/board?${params.toString()}`, { headers });
      if (!res.ok) throw new Error("Failed to fetch jobs");
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch (e) {
      console.error(e);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const t = setTimeout(fetchJobs, 250); // debounce search/typing
    return () => clearTimeout(t);
  }, [fetchJobs]);

  const handleApply = async (jobId: string) => {
    if (hasResume) {
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        await fetch(`/api/v1/candidate-portal/apply`, {
          method: "POST",
          headers,
          body: JSON.stringify({ job_id: jobId })
        });
        // TODO: toast "Applied" + optimistic UI update
      } catch (e) {
        console.error("Apply failed", e);
      }
    } else {
      // TODO: open resume upload modal, then apply
    }
  };

  const renderRequirements = (reqs: any) => {
    if (!reqs) return null;
    if (typeof reqs === "string") return <div className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap">{reqs}</div>;
    
    // If it's the expected dict
    if (typeof reqs === "object" && !Array.isArray(reqs)) {
      return (
        <div className="space-y-3">
          {reqs.education && (
            <div>
              <span className="font-semibold text-zinc-800 text-sm">Education:</span>
              <span className="text-zinc-600 text-sm ml-2">{reqs.education}</span>
            </div>
          )}
          {reqs.experience_years !== undefined && (
            <div>
              <span className="font-semibold text-zinc-800 text-sm">Experience:</span>
              <span className="text-zinc-600 text-sm ml-2">{reqs.experience_years} years</span>
            </div>
          )}
          {reqs.required_skills && reqs.required_skills.length > 0 && (
            <div>
              <span className="font-semibold text-zinc-800 text-sm block mb-1">Required Skills:</span>
              <div className="flex flex-wrap gap-2">
                {reqs.required_skills.map((skill: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 bg-zinc-100 text-zinc-700 text-xs rounded-md border border-zinc-200">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }
    
    return <div className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap">{JSON.stringify(reqs, null, 2)}</div>;
  };

  const renderTextContent = (content: any) => {
    if (!content) return null;
    if (typeof content === "string") {
      return <div className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap">{content}</div>;
    }
    if (Array.isArray(content)) {
      return (
        <ul className="list-disc pl-5 space-y-2 text-zinc-600 text-sm leading-relaxed">
          {content.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
    }
    if (typeof content === "object" && content.raw) {
      return <div className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap">{content.raw}</div>;
    }
    return <div className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap">{JSON.stringify(content, null, 2)}</div>;
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
            <div className="flex justify-between items-start mb-1">
              <h1 className="text-2xl font-bold text-zinc-900">{selected.title}</h1>
              {selected.salary_min && selected.salary_max && (
                <div className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg shadow-sm">
                  <span className="text-emerald-700 font-semibold text-sm">
                    ${selected.salary_min.toLocaleString()} - ${selected.salary_max.toLocaleString()} <span className="text-emerald-600 font-medium text-xs">{selected.currency}</span>
                  </span>
                </div>
              )}
            </div>
            <p className="text-zinc-500">{selected.org_name}</p>
            
            <div className="mt-8 space-y-8">
              {selected.company_description && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-3 border-b border-zinc-100 pb-2">About the Company</h3>
                  {renderTextContent(selected.company_description)}
                </div>
              )}
              
              {selected.key_responsibilities && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-3 border-b border-zinc-100 pb-2">Key Responsibilities</h3>
                  {renderTextContent(selected.key_responsibilities)}
                </div>
              )}
              
              {selected.expectations && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-3 border-b border-zinc-100 pb-2">What We Expect</h3>
                  {renderTextContent(selected.expectations)}
                </div>
              )}
              
              {selected.requirements && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-3 border-b border-zinc-100 pb-2">Requirements</h3>
                  {renderRequirements(selected.requirements)}
                </div>
              )}
              
              {selected.benefits && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-3 border-b border-zinc-100 pb-2">Benefits</h3>
                  {renderTextContent(selected.benefits)}
                </div>
              )}
              
              <div className="pt-6 mt-6 border-t border-zinc-100 flex justify-end">
                <button
                  onClick={() => handleApply(selected.id)}
                  className="px-6 py-2 bg-zinc-900 text-white text-sm font-medium rounded-lg hover:bg-zinc-800 transition-colors"
                >
                  Apply Now
                </button>
              </div>
            </div>
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
