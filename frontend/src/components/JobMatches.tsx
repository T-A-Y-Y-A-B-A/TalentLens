import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import { Loader2, Sparkles, AlertCircle, ChevronDown, ChevronUp, RefreshCw, Briefcase, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MatchGateBar } from "@/components/ui/match-gate-bar";

interface MatchResult {
  candidate_id: string;
  composite_score: number;
  flags: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  interview_questions: string[];
}

interface EnrichedMatch extends MatchResult {
  candidate_name?: string;
  candidate_title?: string; // Fallback or mocked if not available
}

export function JobMatches({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState<"not_started" | "processing" | "done" | "error">("not_started");
  const [matches, setMatches] = useState<EnrichedMatch[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [loadingReasoning, setLoadingReasoning] = useState<Record<string, boolean>>({});

  // Poll for status
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const checkStatus = async () => {
      try {
        const { data, error } = await apiClient.GET("/api/v1/jobs/{job_id}/matches", {
          params: { path: { job_id: jobId } }
        });
        
        if (error) {
          setStatus("error");
          setErrorMsg((error as any).detail || "Failed to check match status.");
          return;
        }

        const res = data as any;
        
        if (res.status === "done") {
          setStatus("done");
          await enrichMatches(res.results || []);
        } else if (res.status === "processing") {
          setStatus("processing");
        } else {
          setStatus("not_started");
        }
      } catch (err: any) {
        setStatus("error");
        setErrorMsg(err.message || "Network error");
      }
    };

    if (status === "processing") {
      // Poll every 3 seconds
      intervalId = setInterval(checkStatus, 3000);
    } else {
      // Just check once on mount
      checkStatus();
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, status]);

  const enrichMatches = async (results: MatchResult[]) => {
    // Fetch candidate details for each match to get their name
    const enriched: EnrichedMatch[] = [...results];
    
    await Promise.all(
      enriched.map(async (match, idx) => {
        try {
          const { data } = await apiClient.GET("/api/v1/candidates/{candidate_id}", {
            params: { path: { candidate_id: match.candidate_id } }
          });
          if (data) {
             enriched[idx].candidate_name = (data as any).name;
          } else {
             enriched[idx].candidate_name = "Unknown Candidate";
          }
        } catch (e) {
          enriched[idx].candidate_name = "Unknown Candidate";
        }
      })
    );
    
    setMatches(enriched);
  };

  const triggerMatch = async () => {
    setStatus("processing");
    setErrorMsg(null);
    try {
      const { error } = await apiClient.POST("/api/v1/jobs/{job_id}/match", {
        params: { path: { job_id: jobId } }
      });
      if (error) {
        setStatus("error");
        setErrorMsg((error as any).detail || "Failed to start matching pipeline.");
      }
    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err.message || "Network error");
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const loadReasoning = async (candidateId: string) => {
    setLoadingReasoning(prev => ({ ...prev, [candidateId]: true }));
    try {
      const token = localStorage.getItem("access_token");
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/matches/${candidateId}/reason`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        }
      });
      
      if (!res.ok) {
        throw new Error("Failed to load reasoning");
      }
      
      const newMatchData = await res.json();
      
      setMatches(prev => prev.map(m => {
        if (m.candidate_id === candidateId) {
          return {
            ...m,
            composite_score: newMatchData.composite_score,
            flags: newMatchData.flags,
            missing_skills: newMatchData.missing_skills,
            strengths: newMatchData.strengths,
            weaknesses: newMatchData.weaknesses,
            recommendation: newMatchData.recommendation,
            interview_questions: newMatchData.interview_questions
          };
        }
        return m;
      }));
    } catch (e) {
      console.error("Failed to load reasoning:", e);
    } finally {
      setLoadingReasoning(prev => ({ ...prev, [candidateId]: false }));
    }
  };

  if (status === "not_started") {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-zinc-200 shadow-sm text-center">
        <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6 border border-indigo-100">
          <Sparkles className="h-8 w-8 text-indigo-600" />
        </div>
        <h3 className="text-xl font-bold text-zinc-900 mb-2">AI Precision Matching</h3>
        <p className="text-zinc-500 max-w-md mb-8">
          Run our hybrid semantic search and LLM-powered matching pipeline to find the most relevant candidates across your entire organization's talent pool.
        </p>
        <Button onClick={triggerMatch} className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-md font-semibold h-11 px-6">
          <Sparkles className="mr-2 h-4 w-4" />
          Run AI Matching Pipeline
        </Button>
      </div>
    );
  }

  if (status === "processing") {
    return (
      <div className="flex flex-col items-center justify-center p-16 bg-white rounded-xl border border-zinc-200 shadow-sm text-center">
        <Loader2 className="h-10 w-10 text-indigo-600 animate-spin mb-6" />
        <h3 className="text-lg font-bold text-zinc-900 mb-2">Analyzing Candidates</h3>
        <p className="text-zinc-500 max-w-md animate-pulse">
          Converting resumes to embeddings, executing hybrid search, and generating LLM reasoning...
        </p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-red-100 shadow-sm text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-bold text-zinc-900 mb-2">Matching Failed</h3>
        <p className="text-red-500 max-w-md mb-6">{errorMsg}</p>
        <Button onClick={triggerMatch} variant="outline" className="font-semibold">
          Try Again
        </Button>
      </div>
    );
  }

  // Done state
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-zinc-200 shadow-sm">
        <div>
          <h3 className="font-bold text-zinc-900 text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-600" /> 
            Ranked Candidates
          </h3>
          <p className="text-sm text-zinc-500">{matches.length} matches found</p>
        </div>
        <Button onClick={triggerMatch} variant="outline" size="sm" className="font-semibold text-zinc-600 border-zinc-300">
          <RefreshCw className="mr-2 h-4 w-4" />
          Re-run AI Matching
        </Button>
      </div>

      {matches.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-zinc-200 shadow-sm">
          <p className="text-zinc-500">No candidates found matching the criteria. Try relaxing strict requirements.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {matches.map((match, index) => {
            const isTopTier = match.composite_score >= 90;
            const isExpanded = !!expandedCards[match.candidate_id];
            
            return (
              <div 
                key={match.candidate_id} 
                className={`flex flex-col sm:flex-row gap-5 p-5 rounded-xl border transition-colors ${
                  isTopTier ? "border-indigo-100 bg-[#F9FAFF]" : "border-zinc-200 bg-white"
                }`}
              >
                {/* Ranking Circle */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold shrink-0 font-serif shadow-sm ${
                  isTopTier ? "bg-indigo-100/80 text-indigo-700" : "bg-zinc-100 text-zinc-600"
                }`}>
                  {index + 1}
                </div>
                
                <div className="flex-1 space-y-4">
                  {/* Header Row */}
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-bold text-zinc-900 font-serif text-lg flex items-center gap-2">
                        {match.candidate_name}
                      </p>
                      <p className="text-[14px] text-zinc-500">Candidate ID: {match.candidate_id.substring(0,8)}</p>
                    </div>
                    <div className={`px-4 py-3 rounded-lg text-xs font-bold shadow-sm min-w-[200px] border flex flex-col gap-2 ${
                      isTopTier ? "bg-indigo-50 border-indigo-100" : "bg-white border-border"
                    }`}>
                      <MatchGateBar 
                        overallScore={Math.round(match.composite_score)} 
                        gateThreshold={75}
                      />
                      
                      {match.flags && match.flags.length > 0 && (
                        <div className="flex flex-col gap-1 items-end mt-1">
                          {match.flags.map(flag => {
                            const label = flag === 'low_relevant_experience' ? 'Low Relevant Experience' :
                                          flag === 'title_mismatch' ? 'Title Mismatch' :
                                          flag === 'incomplete_jd_data' ? 'Incomplete JD Data' :
                                          flag.replace(/_/g, ' ');
                            return (
                              <div key={flag} className="flex items-center px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wide bg-[var(--gate)]/10 text-[var(--gate)] border border-[var(--gate)]/20">
                                {label}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Badges / Missing Skills */}
                  {match.missing_skills && match.missing_skills.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {match.missing_skills.map((skill, i) => (
                         <span key={i} className="text-[11px] uppercase font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-100 tracking-wide">
                           Missing: {skill}
                         </span>
                      ))}
                    </div>
                  )}

                  {/* Strengths / Weaknesses summary (Glanceable) */}
                  <div className="grid sm:grid-cols-2 gap-4">
                     {match.strengths && match.strengths.length > 0 && (
                       <div>
                         <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Strengths</p>
                         <ul className="space-y-1.5">
                           {match.strengths.slice(0, isExpanded ? undefined : 2).map((s, i) => (
                             <li key={i} className="text-sm text-zinc-700 flex items-start gap-2">
                               <div className="w-1.5 h-1.5 rounded-full bg-green-400 mt-1.5 shrink-0" />
                               <span>{s}</span>
                             </li>
                           ))}
                           {!isExpanded && match.strengths.length > 2 && (
                              <li className="text-sm text-zinc-400 italic text-left pl-3.5">+ {match.strengths.length - 2} more</li>
                           )}
                         </ul>
                       </div>
                     )}
                     
                     {match.weaknesses && match.weaknesses.length > 0 && (
                       <div>
                         <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Weaknesses</p>
                         <ul className="space-y-1.5">
                           {match.weaknesses.slice(0, isExpanded ? undefined : 2).map((w, i) => (
                             <li key={i} className="text-sm text-zinc-700 flex items-start gap-2">
                               <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                               <span>{w}</span>
                             </li>
                           ))}
                           {!isExpanded && match.weaknesses.length > 2 && (
                              <li className="text-sm text-zinc-400 italic text-left pl-3.5">+ {match.weaknesses.length - 2} more</li>
                           )}
                         </ul>
                       </div>
                     )}
                  </div>

                  {/* Expandable Content */}
                  {isExpanded && (
                    <div className="pt-4 mt-2 border-t border-zinc-100/80 space-y-5 animate-in slide-in-from-top-2 fade-in duration-200">
                      {(!match.recommendation || match.recommendation === "") ? (
                        <div className="flex flex-col items-center justify-center p-6 bg-zinc-50 rounded-lg border border-zinc-100">
                          {loadingReasoning[match.candidate_id] ? (
                            <div className="flex flex-col items-center">
                              <Loader2 className="h-6 w-6 text-indigo-600 animate-spin mb-3" />
                              <p className="text-sm text-zinc-500">Generating deep AI reasoning...</p>
                            </div>
                          ) : (
                            <div className="text-center">
                              <p className="text-sm text-zinc-600 mb-4">Deep LLM reasoning is available on demand for this candidate.</p>
                              <Button onClick={() => loadReasoning(match.candidate_id)} variant="outline" size="sm" className="font-semibold text-indigo-600 border-indigo-200 hover:bg-indigo-50">
                                <Sparkles className="mr-2 h-4 w-4" /> Load AI Reasoning
                              </Button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <>
                          <div>
                            <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">AI Reasoning</p>
                            <p className="text-sm text-zinc-700 leading-relaxed bg-white/50 p-3 rounded-lg border border-zinc-100">
                              {match.recommendation}
                            </p>
                          </div>
                          
                          {match.interview_questions && match.interview_questions.length > 0 && (
                            <div>
                              <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Suggested Interview Questions</p>
                              <ul className="space-y-2">
                                 {match.interview_questions.map((q, i) => (
                                   <li key={i} className="text-sm text-zinc-700 flex gap-2 p-2 bg-zinc-50 rounded border border-zinc-100">
                                     <span className="font-bold text-zinc-400">{i+1}.</span>
                                     <span>{q}</span>
                                   </li>
                                 ))}
                              </ul>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}

                  <button 
                    onClick={() => toggleExpand(match.candidate_id)}
                    className="w-full py-2 flex items-center justify-center gap-1.5 text-xs font-bold text-zinc-500 hover:text-indigo-600 transition-colors mt-2"
                  >
                    {isExpanded ? (
                      <><ChevronUp size={14} /> Show Less</>
                    ) : (
                      <><ChevronDown size={14} /> Expand AI Reasoning & Details</>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
