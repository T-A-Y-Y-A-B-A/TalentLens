"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Briefcase, MapPin, Building, CheckCircle2, Sparkles, AlertCircle, ArrowLeft, Building2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { useSearchParams, useRouter } from "next/navigation";

type Organization = {
  id: string;
  name: string;
  slug: string;
  plan?: string;
};

type Job = {
  id: string;
  title: string;
  description: string;
  department?: { name: string } | null;
  created_at: string;
  org_id: string;
  match_pct?: number;
  ats_score?: number;
  strengths?: string[];
  weaknesses?: string[];
  missing_skills?: string[];
};

function CandidateJobsContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const orgId = searchParams.get("org_id");
  const router = useRouter();

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [applyingTo, setApplyingTo] = useState<string | null>(null);
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<string>("");
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  const fetchOrgs = async () => {
    try {
      setLoadingOrgs(true);
      const { data, error } = await apiClient.GET("/api/v1/candidate-portal/organizations", {});
      if (data) {
        setOrgs(data as unknown as Organization[]);
      }
    } catch (err) {
      console.error("Failed to fetch orgs", err);
    } finally {
      setLoadingOrgs(false);
    }
  };

  const fetchJobs = async (currentOrgId: string) => {
    try {
      setLoading(true);
      const { data, error } = await apiClient.GET("/api/v1/candidate-portal/jobs", {
        // @ts-ignore
        params: { query: { org_id: currentOrgId } }
      });
      if (data) {
        setJobs(data as unknown as Job[]);
      }
      
      const { data: appsData } = await apiClient.GET("/api/v1/candidate-portal/applications", {});
      if (appsData) {
        const applied = new Set(appsData.map(app => app.job_id));
        setAppliedJobs(applied);
      }
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orgId) {
      fetchJobs(orgId);
    } else {
      fetchOrgs();
    }
  }, [orgId]);

  const handleApply = async (jobId: string) => {
    setApplyingTo(jobId);
    try {
      const { error } = await apiClient.POST("/api/v1/candidate-portal/apply", {
        body: { job_id: jobId }
      });
      
      if (error) {
        toast.error("Application Failed", {
          description: (error as any).detail || "Could not apply to this job."
        });
      } else {
        toast.success("Application Submitted", {
          description: "Your application has been successfully submitted.",
        });
        setAppliedJobs(prev => new Set(prev).add(jobId));
      }
    } catch (err: any) {
      toast.error("Error", {
        description: "An unexpected error occurred."
      });
    } finally {
      setApplyingTo(null);
    }
  };

  const handleAnalyze = async () => {
    if (!orgId) return;
    try {
      setIsAnalyzing(true);
      setAnalysisStatus("Initiating analysis...");
      const { data, error } = await apiClient.POST("/api/v1/candidate-portal/me/analyze", {
        // @ts-ignore
        body: { org_id: orgId }
      });

      if (error) {
        toast.error("Analysis Failed", { description: (error as any).detail || "Could not start analysis" });
        setIsAnalyzing(false);
        return;
      }

      if (data && (data as any).task_id) {
        setAnalysisStatus("Analyzing resume against open jobs...");
        pollAnalysisStatus((data as any).task_id as string);
      }
    } catch (err) {
      toast.error("Error", { description: "Unexpected error starting analysis" });
      setIsAnalyzing(false);
    }
  };

  const pollAnalysisStatus = async (taskId: string) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const { data } = await apiClient.GET("/api/v1/candidate-portal/me/analyze/status/{task_id}", {
          params: { path: { task_id: taskId } }
        });
        
        if ((data as any)?.ready) {
          clearInterval(interval);
          setAnalysisStatus("Analysis complete!");
          toast.success("Job Analysis Complete");
          setTimeout(() => {
            setIsAnalyzing(false);
            if ((data as any).matched_jobs) {
              setJobs((data as any).matched_jobs);
            } else if (orgId) {
              fetchJobs(orgId);
            }
          }, 1000);
        } else if (attempts > 30) {
          // Timeout after ~1 minute
          clearInterval(interval);
          setIsAnalyzing(false);
          toast.error("Analysis Timeout", { description: "Analysis is taking too long. Check back later." });
        } else {
          // Update loading message to simulate stages
          if (attempts === 4) setAnalysisStatus("Generating embeddings...");
          if (attempts === 8) setAnalysisStatus("Running hybrid search...");
          if (attempts === 12) setAnalysisStatus("Cross-encoder reranking...");
          if (attempts === 16) setAnalysisStatus("Evaluating matches with LLM...");
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);
  };

  if (!orgId) {
    if (loadingOrgs) {
      return (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Explore Companies</h1>
          <p className="text-zinc-500 mt-2">Select an organization to view their open positions.</p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {orgs.map(org => (
            <Card 
              key={org.id} 
              className="cursor-pointer hover:border-indigo-400 hover:shadow-md transition-all group" 
              onClick={() => router.push(`/portal/jobs?org_id=${org.id}`)}
            >
              <CardContent className="p-6 flex items-start gap-4">
                <div className="h-12 w-12 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-100 transition-colors">
                  <Building2 className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-zinc-900">{org.name}</h3>
                  <p className="text-sm text-zinc-500 mt-1">View opportunities</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (loading && jobs.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Button 
        variant="ghost" 
        onClick={() => router.push("/portal/jobs")} 
        className="pl-0 text-zinc-500 hover:text-zinc-900 hover:bg-transparent -mb-2"
      >
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Companies
      </Button>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Job Board</h1>
          <p className="text-zinc-500 mt-2">Discover and apply to the latest opportunities.</p>
        </div>
        
        <Button 
          onClick={handleAnalyze} 
          disabled={isAnalyzing || jobs.length === 0}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-md"
        >
          {isAnalyzing ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> {analysisStatus}</>
          ) : (
            <><Sparkles className="mr-2 h-4 w-4" /> AI Job Match</>
          )}
        </Button>
      </div>

      {jobs.length === 0 ? (
        <Card className="bg-zinc-50 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="h-12 w-12 text-zinc-300 mb-4" />
            <h3 className="text-lg font-medium text-zinc-900">No open positions</h3>
            <p className="text-zinc-500 mt-1">Check back later for new opportunities.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {jobs.map((job) => {
            const isApplied = appliedJobs.has(job.id);
            const hasMatch = job.match_pct !== undefined && job.match_pct !== null;
            const isExpanded = expandedJob === job.id;
            
            return (
              <Card key={job.id} className={`flex flex-col transition-all hover:shadow-lg ${hasMatch && job.match_pct! >= 75 ? 'border-indigo-200' : ''}`}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="line-clamp-1 text-xl">{job.title}</CardTitle>
                      <CardDescription className="flex items-center gap-4 mt-2">
                        {job.department && (
                          <span className="flex items-center gap-1.5 text-xs font-medium text-zinc-600">
                            <Building className="h-3.5 w-3.5" />
                            {job.department.name}
                          </span>
                        )}
                        <span className="flex items-center gap-1.5 text-xs font-medium text-zinc-600">
                          <MapPin className="h-3.5 w-3.5" />
                          Remote
                        </span>
                      </CardDescription>
                    </div>
                    
                    {hasMatch && (
                      <div className="flex flex-col items-end">
                        <Badge variant={job.match_pct! >= 80 ? "default" : job.match_pct! >= 50 ? "secondary" : "outline"} 
                               className={job.match_pct! >= 80 ? 'bg-indigo-600' : ''}>
                          {Math.round(job.match_pct!)}% Match
                        </Badge>
                        {job.ats_score !== undefined && (
                          <span className="text-[10px] text-zinc-400 mt-1 font-medium">
                            ATS: {job.ats_score}%
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </CardHeader>
                
                <CardContent className="flex-1 space-y-4">
                  <p className={`text-sm text-zinc-600 ${isExpanded ? '' : 'line-clamp-3'}`}>
                    {job.description}
                  </p>
                  
                  {hasMatch && isExpanded && (
                    <div className="bg-indigo-50/50 rounded-lg p-4 space-y-3 border border-indigo-100/50 mt-4 animate-in fade-in slide-in-from-top-2 duration-200">
                      {job.strengths && job.strengths.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-indigo-900 uppercase tracking-wider mb-1.5">Strengths</h4>
                          <ul className="text-sm text-zinc-700 space-y-1 list-disc pl-4 marker:text-indigo-400">
                            {job.strengths.map((s, i) => <li key={i}>{s}</li>)}
                          </ul>
                        </div>
                      )}
                      
                      {job.missing_skills && job.missing_skills.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                            <AlertCircle className="h-3 w-3" /> Missing Skills
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {job.missing_skills.map((s, i) => (
                              <Badge key={i} variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-xs font-normal py-0">
                                {s}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
                
                <CardFooter className="flex gap-3 bg-zinc-50/50 pt-4 border-t border-zinc-100">
                  <Button 
                    className={`flex-1 ${isApplied ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' : 'bg-zinc-900 hover:bg-zinc-800 text-white'}`}
                    variant={isApplied ? "outline" : "default"}
                    onClick={() => handleApply(job.id)}
                    disabled={isApplied || applyingTo === job.id}
                  >
                    {applyingTo === job.id ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Applying...</>
                    ) : isApplied ? (
                      <><CheckCircle2 className="mr-2 h-4 w-4" /> Applied</>
                    ) : (
                      'Apply Now'
                    )}
                  </Button>
                  
                  {hasMatch && (
                    <Button 
                      variant="ghost" 
                      onClick={() => setExpandedJob(isExpanded ? null : job.id)}
                      className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                    >
                      {isExpanded ? 'Hide Details' : 'View Match Details'}
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function CandidateJobsPage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-64"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>}>
      <CandidateJobsContent />
    </Suspense>
  );
}
