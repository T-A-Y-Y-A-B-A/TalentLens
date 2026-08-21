"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Mail, Phone, Calendar, Briefcase, FileText, ChevronLeft, Sparkles, CheckCircle, Upload, Download, Award, GraduationCap } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { MatchGateBar } from "@/components/ui/match-gate-bar";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

import { components } from "@/lib/api/schema";

type CandidateRead = components["schemas"]["CandidateRead"];
type ApplicationRead = components["schemas"]["ApplicationRead"];
type JobRead = components["schemas"]["JobRead"];
type MatchResult = {
  candidate_id: string;
  job_id: string;
  composite_score: number;
  flags: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  interview_questions: string[];
};

export default function CandidateDetailPage() {
  const params = useParams();
  const candidateId = params.id as string;
  
  const [candidate, setCandidate] = useState<CandidateRead | null>(null);
  const [applications, setApplications] = useState<ApplicationRead[]>([]);
  const [matchResults, setMatchResults] = useState<Record<string, MatchResult>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add to Job State
  const [jobs, setJobs] = useState<JobRead[]>([]);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [isAdding, setIsAdding] = useState(false);

  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const fetchCandidateData = async () => {
      try {
        const { data: candData, error: candErr } = await apiClient.GET("/api/v1/candidates/{candidate_id}", {
          params: { path: { candidate_id: candidateId } }
        });
        if (candErr) throw candErr;
        
        let candidateWithData = { ...candData } as any;
        
        // Fetch parsed data if resume exists
        if (candData && (candData as any).resume) {
          try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`/api/v1/candidates/${candidateId}/resume/${(candData as any).resume.id}/parsed`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
              const parsedData = await res.json();
              candidateWithData.parsed_data = parsedData;
            }
          } catch (e) {
            console.error("Failed to fetch parsed data", e);
          }
        }
        
        setCandidate(candidateWithData);

        const { data: appData, error: appErr } = await apiClient.GET("/api/v1/applications", {
          params: { query: { candidate_id: candidateId } }
        });
        if (appErr) throw appErr;
        
        const apps = (appData as any as ApplicationRead[]) || [];
        setApplications(apps);

        // Fetch matches for each application
        const matches: Record<string, MatchResult> = {};
        for (const app of apps) {
          const { data: matchData } = await apiClient.GET("/api/v1/applications/{application_id}/match-result", {
            // @ts-ignore
            params: { path: { application_id: app.id } }
          });
          
          if (matchData) {
            matches[app.job_id] = matchData as any as MatchResult;
          }
        }
        setMatchResults(matches);

        // Fetch jobs for the "Add to Job" dropdown
        const { data: jobsData } = await apiClient.GET("/api/v1/jobs", {});
        if (jobsData) {
          setJobs(jobsData as any as JobRead[]);
        }

      } catch (err: any) {
        setError(err.message || "Failed to load candidate details");
      } finally {
        setLoading(false);
      }
    };

  useEffect(() => {
    if (candidateId) fetchCandidateData();
  }, [candidateId]);

  const handleReject = async (appId: string) => {
    if (!confirm("Are you sure you want to reject this application? This cannot be undone.")) return;
    setRejectingId(appId);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/applications/${appId}/reject`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        await fetchCandidateData();
      } else {
        alert("Failed to reject application.");
      }
    } catch (err) {
      console.error(err);
      alert("Error rejecting application.");
    } finally {
      setRejectingId(null);
    }
  };

  const handleAddToJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJobId) return;

    setIsAdding(true);
    try {
      const { data, error: applyErr } = await apiClient.POST("/api/v1/applications", {
        body: { candidate_id: candidateId, job_id: selectedJobId }
      });

      if (applyErr) {
        const errorMessage = (applyErr as any).error?.message || (applyErr as any).detail || "Failed to add candidate to job";
        throw new Error(errorMessage);
      }

      // Success, add to the local list
      if (data) {
        setApplications([...applications, data as any as ApplicationRead]);
        setIsAddOpen(false);
        setSelectedJobId("");
      }
    } catch (err: any) {
      alert(err.message || "An error occurred");
    } finally {
      setIsAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-10rem)]">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="text-center py-8 text-red-500">
        {error || "Candidate not found"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center">
        <Link href="/dashboard/candidates" className="text-gray-500 hover:text-gray-700 mr-4">
          <ChevronLeft className="h-5 w-5" />
        </Link>
        <div className="flex flex-1 items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              {candidate.name}
            </h1>
            <p className="text-sm text-gray-500 capitalize">{candidate.source?.replace("_", " ") || "Direct"} Candidate</p>
          </div>
          
          <div className="flex items-center gap-3">
            {(candidate as any).resume && (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center text-sm text-green-600 font-medium bg-green-50 px-2 py-1 rounded-md border border-green-200">
                  <CheckCircle className="mr-1 h-4 w-4" />
                  Resume Uploaded
                </span>
                <Button 
                  onClick={(e) => {
                    e.stopPropagation();
                    const token = localStorage.getItem("access_token");
                    const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/candidates/${candidateId}/resume/${(candidate as any).resume.id}/download`;
                    fetch(downloadUrl, { headers: { "Authorization": `Bearer ${token}` } })
                      .then(async res => {
                        if (!res.ok) throw new Error("Failed to download");
                        const blob = await res.blob();
                        const url = window.URL.createObjectURL(blob);
                        window.open(url, "_blank");
                        setTimeout(() => window.URL.revokeObjectURL(url), 5000);
                      })
                      .catch(() => alert("Failed to download resume"));
                  }}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground text-zinc-900 h-9 px-4 py-2"
                  variant="outline"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Resume
                </Button>
              </div>
            )}

            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
              <DialogTrigger render={
                <Button className="bg-indigo-600 hover:bg-indigo-700">
                  <Briefcase className="mr-2 h-4 w-4" />
                  Add to Job
                </Button>
              } />
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Candidate to Job Pipeline</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddToJob} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Select Job</Label>
                    <Select value={selectedJobId} onValueChange={(val) => setSelectedJobId(val || "")}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a job..." />
                      </SelectTrigger>
                      <SelectContent>
                        {jobs.filter(j => j.status === "open").map(job => (
                          <SelectItem key={job.id} value={job.id}>
                            {job.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>Cancel</Button>
                    <Button type="submit" disabled={!selectedJobId || isAdding} className="bg-indigo-600 hover:bg-indigo-700">
                      {isAdding && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Add Candidate
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Info */}
        <div className="col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center text-sm">
                <Mail className="h-4 w-4 text-gray-400 mr-3 shrink-0" />
                <span className="text-gray-900">{candidate.email}</span>
              </div>
              {candidate.phone && (
                <div className="flex items-center text-sm">
                  <Phone className="h-4 w-4 text-gray-400 mr-3 shrink-0" />
                  <span className="text-gray-900">{candidate.phone}</span>
                </div>
              )}
              <div className="flex items-center text-sm">
                <Calendar className="h-4 w-4 text-gray-400 mr-3 shrink-0" />
                <span className="text-gray-900">Added on {new Date(candidate.created_at).toLocaleDateString()}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Applications & AI Match */}
        <div className="col-span-1 md:col-span-2 space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Applications & AI Matching</h2>
          
          {applications.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                This candidate has not applied to any jobs yet.
              </CardContent>
            </Card>
          ) : (
            applications.map(app => {
              const match = matchResults[app.job_id];
              return (
                <Card key={app.id} className="overflow-hidden">
                  <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <div className="flex items-center">
                      <Briefcase className="h-5 w-5 text-gray-400 mr-2" />
                      <span className="font-medium text-gray-900">Job ID: {app.job_id.slice(0, 8)}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Status: {app.status || "active"} | Stage ID: {app.current_stage_id ? app.current_stage_id.slice(0, 8) : "Initial"}
                      </span>
                      {!["rejected", "withdrawn", "hired"].includes((app.status || "").toLowerCase()) && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700"
                          onClick={() => handleReject(app.id)}
                          disabled={rejectingId === app.id}
                        >
                          {rejectingId === app.id ? "Rejecting..." : "Reject"}
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <CardContent className="p-6">
                    {match ? (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-2 max-w-sm">
                          <div className="flex items-center gap-2 mb-2">
                            <Sparkles className="h-5 w-5 text-indigo-500" />
                            <h3 className="text-lg font-semibold text-indigo-900">AI Match Score</h3>
                          </div>
                          <MatchGateBar overallScore={Math.round(match.composite_score)} gateThreshold={75} />
                        </div>
                        
                        <div className="bg-indigo-50/50 p-4 rounded-lg border border-indigo-100">
                          <p className="text-sm text-gray-800 italic">"{match.recommendation}"</p>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                          <div>
                            <h4 className="text-sm font-semibold text-green-700 mb-2">Strengths</h4>
                            <ul className="list-disc pl-4 space-y-1 text-sm text-gray-600">
                              {match.strengths.map((s, i) => <li key={i}>{s}</li>)}
                            </ul>
                          </div>
                          <div>
                            <h4 className="text-sm font-semibold text-red-700 mb-2">Weaknesses / Missing</h4>
                            <ul className="list-disc pl-4 space-y-1 text-sm text-gray-600">
                              {match.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                              {match.missing_skills.map((m, i) => <li key={`m-${i}`}>{m}</li>)}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ) : candidate.parsed_data ? (
                      <>
                        <h4 className="text-md font-semibold text-gray-800 mb-4 flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" /> Candidate Summary
                        </h4>
                        <div className="space-y-6">
                          {/* Skills */}
                          <div className="border border-gray-100 rounded-lg p-4 bg-white shadow-sm">
                            <h4 className="flex items-center gap-2 text-sm font-semibold text-indigo-600 mb-3">
                              <Award className="h-4 w-4" /> Top Skills
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {candidate.parsed_data.skills.map((skill: string, i: number) => (
                                <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>

                          {/* Experience */}
                          <div className="border border-gray-100 rounded-lg p-4 bg-white shadow-sm">
                            <h4 className="flex items-center gap-2 text-sm font-semibold text-indigo-600 mb-4">
                              <Briefcase className="h-4 w-4" /> Experience
                            </h4>
                            <div className="space-y-6">
                              {candidate.parsed_data.experience.map((exp: any, i: number) => (
                                <div key={i} className="relative pl-6 border-l-2 border-zinc-100 last:border-0 last:pb-0 pb-6">
                                  <div className="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-zinc-300 ring-4 ring-white" />
                                  <h4 className="text-sm font-bold text-zinc-900">{exp.title}</h4>
                                  <p className="text-sm font-medium text-indigo-600">{exp.company}</p>
                                  <p className="text-xs text-zinc-500 mt-1 mb-2">
                                    {exp.start_date || 'Unknown'} - {exp.end_date || 'Present'}
                                  </p>
                                  {exp.description && (
                                    <p className="text-sm text-zinc-600 line-clamp-3">{exp.description}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          {/* Education */}
                          <div className="border border-gray-100 rounded-lg p-4 bg-white shadow-sm">
                            <h4 className="flex items-center gap-2 text-sm font-semibold text-indigo-600 mb-4">
                              <GraduationCap className="h-4 w-4" /> Education
                            </h4>
                            <div className="space-y-4">
                              {candidate.parsed_data.education.map((edu: any, i: number) => (
                                <div key={i} className="flex justify-between items-start">
                                  <div>
                                    <h4 className="text-sm font-bold text-zinc-900">{edu.degree}</h4>
                                    <p className="text-sm text-zinc-600">{edu.institution}</p>
                                  </div>
                                  <span className="text-xs font-medium bg-zinc-100 text-zinc-600 px-2 py-1 rounded">
                                    {edu.graduation_year || 'Unknown'}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-6 text-gray-500">
                        <Sparkles className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                        <p>No AI Match data available for this application.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
