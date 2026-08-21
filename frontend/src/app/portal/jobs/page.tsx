"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { JobCard, JobCardData } from "./JobCard";
import { FilterBar, JobBoardFilters } from "./FilterBar";
import { useAuth } from "@/components/providers/AuthProvider";
import { MatchGateBar } from "@/components/ui/match-gate-bar";

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
    <div className="flex h-screen bg-background">
      {/* Left: filterable list */}
      <div className="flex w-full max-w-md flex-col border-r border-border bg-card lg:max-w-lg">
        <FilterBar
          filters={filters}
          onChange={setFilters}
          hasResume={hasResume}
          resultCount={jobs.length}
        />
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {loading && (
            <div className="py-12 text-center text-sm text-muted-foreground">Loading roles...</div>
          )}
          {!loading && jobs.length === 0 && (
            <div className="py-12 text-center text-sm text-muted-foreground">
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
      <div className="hidden flex-1 overflow-y-auto p-8 bg-background lg:block">
        {!selected ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            Select a role to see full details
          </div>
        ) : (
          <div className="mx-auto max-w-4xl bg-card p-10 rounded-2xl shadow-sm border border-border">
            <div className="flex justify-between items-start mb-2">
              <h1 className="text-3xl font-bold text-foreground">{selected.title}</h1>
              {selected.salary_min && selected.salary_max && (
                <div className="px-4 py-2 bg-accent border border-border rounded-lg shadow-sm">
                  <span className="text-primary font-bold font-mono text-sm">
                    ${selected.salary_min.toLocaleString()} - ${selected.salary_max.toLocaleString()} <span className="text-muted-foreground font-medium text-xs">{selected.currency}</span>
                  </span>
                </div>
              )}
            </div>
            <p className="text-lg text-muted-foreground mb-8">{selected.org_name}</p>
            
            <div className="space-y-10">
              {selected.company_description && (
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 mb-4 border-b border-zinc-100 pb-2">About the Company</h3>
                  {renderTextContent(selected.company_description)}
                </div>
              )}
              
              {selected.key_responsibilities && (
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 mb-4 border-b border-zinc-100 pb-2">Key Responsibilities</h3>
                  {renderTextContent(selected.key_responsibilities)}
                </div>
              )}
              
              {selected.expectations && (
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 mb-4 border-b border-zinc-100 pb-2">What We Expect</h3>
                  {renderTextContent(selected.expectations)}
                </div>
              )}
              
              {selected.requirements && (
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 mb-4 border-b border-zinc-100 pb-2">Requirements</h3>
                  {renderRequirements(selected.requirements)}
                </div>
              )}
              
              {selected.benefits && (
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 mb-4 border-b border-zinc-100 pb-2">Benefits</h3>
                  {renderTextContent(selected.benefits)}
                </div>
              )}

              {/* AI Match Report Section */}
              {hasResume && selected.composite_score !== null && (
                <div className="mt-12 pt-8 border-t-2 border-border">
                  <div className="bg-gradient-to-br from-[var(--signal-light)] to-background p-8 rounded-2xl border border-[var(--slate-light)] shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-[var(--signal)]"></div>
                    
                    <div className="flex flex-col mb-6 gap-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[var(--signal-light)] rounded-lg text-[var(--signal)]">
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                        </div>
                        <h3 className="text-2xl font-bold text-foreground">AI Match Analysis</h3>
                      </div>
                      
                      <div className="mt-4 max-w-sm">
                        <MatchGateBar overallScore={Math.round(selected.composite_score)} gateThreshold={75} />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Strengths */}
                      <div>
                        <h4 className="text-sm font-bold text-emerald-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                          Matched Strengths
                        </h4>
                        {selected.matched_skills && selected.matched_skills.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {selected.matched_skills.map((skill: string, i: number) => (
                              <span key={i} className="px-3 py-1.5 bg-emerald-100 text-emerald-800 text-sm font-medium rounded-lg border border-emerald-200">
                                {skill}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-zinc-500 text-sm italic">No direct skill matches identified in your profile.</p>
                        )}
                      </div>

                      {/* Gaps */}
                      <div>
                        <h4 className="text-sm font-bold text-rose-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                          Skill Gaps
                        </h4>
                        {selected.missing_skills && selected.missing_skills.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {selected.missing_skills.map((skill: string, i: number) => (
                              <span key={i} className="px-3 py-1.5 bg-rose-50 text-rose-700 text-sm font-medium rounded-lg border border-rose-200 opacity-90">
                                {skill}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-emerald-600 text-sm font-medium">No missing skills detected! You cover all requirements.</p>
                        )}
                      </div>
                    </div>

                    {/* AI Insights (Flags) */}
                    {selected.flags && selected.flags.length > 0 && (
                      <div className="mt-8 pt-6 border-t border-indigo-100/50">
                        <h4 className="text-sm font-bold text-indigo-900 uppercase tracking-wider mb-3">AI Insights</h4>
                        <ul className="space-y-2">
                          {selected.flags.includes("low_relevant_experience") && (
                            <li className="flex items-start gap-2 text-sm text-indigo-800 bg-indigo-50/80 p-3 rounded-lg border border-indigo-100">
                              <span className="text-indigo-500 mt-0.5">•</span> 
                              <span>Your past job titles suggest you may have limited direct experience in this specific domain, which impacted your match score. Highlight any transferable projects in your cover letter.</span>
                            </li>
                          )}
                          {selected.flags.includes("title_mismatch") && (
                            <li className="flex items-start gap-2 text-sm text-indigo-800 bg-indigo-50/80 p-3 rounded-lg border border-indigo-100">
                              <span className="text-indigo-500 mt-0.5">•</span> 
                              <span>Your recent job titles don't strongly align with this role's title. Be prepared to explain your career pivot or how your current skills apply.</span>
                            </li>
                          )}
                          {selected.flags.includes("incomplete_jd_data") && (
                            <li className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50/80 p-3 rounded-lg border border-amber-100">
                              <span className="text-amber-500 mt-0.5">•</span> 
                              <span>The employer provided limited details for this job, so this match score relies heavily on keyword requirements rather than deep semantic analysis.</span>
                            </li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="pt-8 mt-8 border-t-2 border-zinc-100 flex justify-end">
                <button
                  onClick={() => handleApply(selected.id)}
                  className="px-8 py-3.5 bg-zinc-900 text-white text-base font-bold rounded-xl hover:bg-zinc-800 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200"
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
