"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Briefcase, MapPin, Building, CheckCircle2, Sparkles, AlertCircle, ArrowLeft, Building2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { useSearchParams, useRouter } from "next/navigation";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SplitLayout } from "@/components/JobBoard/SplitLayout";
import { AutoFillResume } from "@/components/JobBoard/AutoFillResume";

type Job = {
  id: string;
  title: string;
  description: string;
  requirements?: string[] | Record<string, any>;
  department?: { name: string } | null;
  created_at: string;
  org_id: string;
  organization_name?: string;
  work_type?: string;
  match_pct?: number;
  ats_score?: number;
  strengths?: string[];
  weaknesses?: string[];
  missing_skills?: string[];
};

function formatWorkType(wt?: string) {
  if (!wt) return "Remote";
  return wt.charAt(0) + wt.slice(1).toLowerCase();
}

function CandidateJobsContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const orgId = searchParams.get("org_id");
  const router = useRouter();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());
  const [resumeRequired, setResumeRequired] = useState(false);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<string>("");

  // Modals state
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [matchExplanation, setMatchExplanation] = useState<string | null>(null);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  
  const [applyJob, setApplyJob] = useState<Job | null>(null);
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const queryParams: any = {};
      if (orgId) {
        queryParams.org_id = orgId;
      }
      const { data, error } = await apiClient.GET("/api/v1/candidate-portal/jobs", {
        // @ts-ignore
        params: { query: queryParams }
      });
      if (data && (data as any).jobs) {
        setJobs((data as any).jobs as Job[]);
        if ((data as any).status === "resume_required") {
          setResumeRequired(true);
        } else {
          setResumeRequired(false);
        }
      } else if (Array.isArray(data)) {
        setJobs(data as unknown as Job[]);
        setResumeRequired(false);
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
    fetchJobs();
  }, [orgId]);

  const handleAnalyze = async () => {
    // We only trigger analysis for the first job's org as a fallback, or if we have an orgId
    const targetOrgId = orgId || (jobs.length > 0 ? jobs[0].org_id : null);
    if (!targetOrgId) return;
    
    try {
      setIsAnalyzing(true);
      setAnalysisStatus("Initiating analysis...");
      const { data, error } = await apiClient.POST("/api/v1/candidate-portal/me/analyze", {
        // @ts-ignore
        body: { org_id: targetOrgId }
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
            fetchJobs();
          }, 1000);
        } else if (attempts > 30) {
          clearInterval(interval);
          setIsAnalyzing(false);
          toast.error("Analysis Timeout", { description: "Analysis is taking too long." });
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);
  };

  const openDetails = async (job: Job) => {
    setSelectedJob(job);
    setIsDetailsModalOpen(true);
    setMatchExplanation(null);
    
    if (job.match_pct !== undefined && job.match_pct !== null) {
      setIsLoadingExplanation(true);
      try {
        const { data } = await apiClient.GET("/api/v1/candidate-portal/jobs/{job_id}/match-explanation" as any, {
          params: { path: { job_id: job.id } }
        });
        if (data && (data as any).explanation) {
          setMatchExplanation((data as any).explanation);
        }
      } catch (err) {
        console.error("Failed to fetch match explanation", err);
      } finally {
        setIsLoadingExplanation(false);
      }
    }
  };

  const openApply = (job: Job, e: React.MouseEvent) => {
    e.stopPropagation();
    setApplyJob(job);
    setIsApplyModalOpen(true);
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {orgId && (
        <Button 
          variant="ghost" 
          onClick={() => router.push("/portal/jobs")} 
          className="pl-0 text-zinc-500 hover:text-zinc-900 hover:bg-transparent -mb-2"
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> View All Companies
        </Button>
      )}

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

      {resumeRequired ? (
        <Card className="bg-zinc-50 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-amber-500 mb-4" />
            <h3 className="text-lg font-medium text-zinc-900">No resume uploaded</h3>
            <p className="text-zinc-500 mt-1">Upload your resume first to see matched jobs.</p>
            <Button className="mt-4 bg-indigo-600 hover:bg-indigo-700" onClick={() => router.push("/portal/profile")}>Go to Profile to Upload</Button>
          </CardContent>
        </Card>
      ) : jobs.length === 0 ? (
        <Card className="bg-zinc-50 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="h-12 w-12 text-zinc-300 mb-4" />
            <h3 className="text-lg font-medium text-zinc-900">No open positions</h3>
            <p className="text-zinc-500 mt-1">Check back later for new opportunities.</p>
          </CardContent>
        </Card>
      ) : (
        <SplitLayout 
          jobs={jobs} 
          selectedJob={selectedJob} 
          onSelectJob={setSelectedJob} 
          onApply={(job) => openApply(job as Job, { stopPropagation: () => {} } as any)} 
          appliedJobs={appliedJobs} 
        />
      )}

      {/* Job Details Modal */}
      {selectedJob && (
        <Dialog open={isDetailsModalOpen} onOpenChange={setIsDetailsModalOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl">{selectedJob.title}</DialogTitle>
              <DialogDescription className="flex gap-4 mt-2 text-sm font-medium text-zinc-600">
                {selectedJob.department && (
                  <span className="flex items-center gap-1.5">
                    <Building className="h-4 w-4" /> {selectedJob.department.name}
                  </span>
                )}
                {selectedJob.organization_name && (
                  <span className="flex items-center gap-1.5">
                    <Building className="h-4 w-4" /> {selectedJob.organization_name}
                  </span>
                )}
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" /> {formatWorkType(selectedJob.work_type)}
                </span>
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4 space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 mb-2">Description</h3>
                <p className="text-zinc-700 whitespace-pre-wrap">{selectedJob.description}</p>
              </div>

              {selectedJob.requirements && (
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 mb-2">Requirements</h3>
                  <div className="space-y-4">
                    {/* Required Skills */}
                    {(selectedJob.requirements as any).required_skills && (selectedJob.requirements as any).required_skills.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-zinc-800 mb-1.5">Required Skills</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {(selectedJob.requirements as any).required_skills.map((skill: string, i: number) => (
                            <Badge key={i} variant="outline" className="bg-zinc-50 text-zinc-700 border-zinc-200">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Experience */}
                    {(selectedJob.requirements as any).experience_years !== undefined && (selectedJob.requirements as any).experience_years !== null && (
                      <div>
                        <h4 className="text-sm font-medium text-zinc-800 mb-1">Experience</h4>
                        <p className="text-sm text-zinc-700">{(selectedJob.requirements as any).experience_years}+ years</p>
                      </div>
                    )}

                    {/* Education */}
                    {(selectedJob.requirements as any).education && (
                      <div>
                        <h4 className="text-sm font-medium text-zinc-800 mb-1">Education</h4>
                        <p className="text-sm text-zinc-700">{(selectedJob.requirements as any).education}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedJob.match_pct !== undefined && selectedJob.match_pct !== null && (
                <div className="bg-indigo-50/50 rounded-lg p-4 border border-indigo-100/50">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="h-5 w-5 text-indigo-600" />
                    <h3 className="font-semibold text-indigo-900">AI Match Analysis ({Math.round(selectedJob.match_pct)}%)</h3>
                  </div>
                  {selectedJob.strengths && selectedJob.strengths.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-xs font-semibold text-indigo-900 uppercase mb-1">Strengths</h4>
                      <ul className="text-sm text-zinc-700 list-disc pl-4 marker:text-indigo-400">
                        {selectedJob.strengths.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  {selectedJob.missing_skills && selectedJob.missing_skills.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-amber-800 uppercase mb-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> Missing Skills
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedJob.missing_skills.map((s, i) => (
                          <Badge key={i} variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {isLoadingExplanation ? (
                    <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600 bg-white/40 p-3 rounded-md border border-indigo-100/50">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating AI match explanation...
                    </div>
                  ) : matchExplanation ? (
                    <div className="mt-4 p-3 bg-white/60 rounded-md border border-indigo-100 text-sm text-zinc-800 leading-relaxed italic">
                      {matchExplanation}
                    </div>
                  ) : null}
                </div>
              )}
            </div>
            <div className="mt-6 flex justify-end">
               <Button 
                  className="bg-zinc-900 text-white hover:bg-zinc-800"
                  onClick={() => {
                    setIsDetailsModalOpen(false);
                    openApply(selectedJob, { stopPropagation: () => {} } as any);
                  }}
                  disabled={appliedJobs.has(selectedJob.id)}
               >
                 {appliedJobs.has(selectedJob.id) ? "Applied" : "Apply Now"}
               </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Apply Modal */}
      {applyJob && (
        <ApplyModal 
          job={applyJob}
          isOpen={isApplyModalOpen}
          onClose={() => setIsApplyModalOpen(false)}
          onSuccess={() => {
            setAppliedJobs(prev => new Set(prev).add(applyJob.id));
            setIsApplyModalOpen(false);
          }}
          user={user}
        />
      )}
    </div>
  );
}

function ApplyModal({ job, isOpen, onClose, onSuccess, user }: { job: Job, isOpen: boolean, onClose: () => void, onSuccess: () => void, user: any }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [missingFields, setMissingFields] = useState<string[]>([]);
  
  const [name, setName] = useState(user?.name || "");
  const [phone, setPhone] = useState("");
  
  const [education, setEducation] = useState([{ degree: "", institution: "", field_of_study: "" }]);
  const [experience, setExperience] = useState([{ role: "", company: "", duration: "" }]);
  const [certifications, setCertifications] = useState([{ name: "", issuing_body: "" }]);
  
  const [file, setFile] = useState<File | null>(null);
  const [resumeUploaded, setResumeUploaded] = useState(false); // IDEMPOTENCY FLAG

  useEffect(() => {
    if (isOpen) {
      setErrorMsg("");
      setIsSubmitting(false);
      setMissingFields([]);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setMissingFields([]);

    // Clean up dynamic lists first
    const cleanEdu = education.filter(e => e.degree || e.institution);
    const cleanExp = experience.filter(e => e.role || e.company);
    const cleanCerts = certifications.filter(c => c.name);

    // Required-field validation
    const missing: string[] = [];
    if (!phone.trim()) missing.push("phone");
    if (!file && !resumeUploaded) missing.push("resume");
    if (cleanEdu.length === 0) missing.push("education");

    if (missing.length > 0) {
      setMissingFields(missing);
      setErrorMsg(`Please fill in: ${missing.join(", ")}`);
      return; // block submission entirely
    }

    setIsSubmitting(true);

    try {
      // Step 1: Upload resume if provided and not yet uploaded
      if (file && !resumeUploaded) {
        const formData = new FormData();
        formData.append("file", file);
        
        const token = localStorage.getItem('access_token');
        const response = await fetch("/api/v1/candidate-portal/resume", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          },
          body: formData
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to upload resume");
        }
        setResumeUploaded(true);
      }

      // Step 2: Apply
      const { error } = await apiClient.POST("/api/v1/candidate-portal/apply", {
        body: {
          job_id: job.id,
          name: name,
          phone: phone,
          education: cleanEdu.length > 0 ? cleanEdu : [],
          work_experience: cleanExp.length > 0 ? cleanExp : undefined,
          certifications: cleanCerts.length > 0 ? cleanCerts : undefined
        }
      });

      if (error) {
        let errMsg = "Failed to submit application";
        if ((error as any).detail) {
          if (Array.isArray((error as any).detail)) {
            errMsg = (error as any).detail.map((e: any) => e.msg).join(", ");
          } else {
            errMsg = (error as any).detail;
          }
        }
        throw new Error(errMsg);
      }

      toast.success("Application Submitted successfully!");
      onSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Apply for {job.title}</DialogTitle>
          <DialogDescription>Please provide your details below.</DialogDescription>
        </DialogHeader>
        
        {errorMsg && (
          <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4 border border-red-200">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <AutoFillResume 
            onFileSelected={setFile} 
            onExtractedData={(data: any) => { 
              setName(data.name || name); 
              setPhone(data.phone || phone); 
              if(data.education) setEducation(data.education); 
              if(data.experience) setExperience(data.experience); 
              setResumeUploaded(true); 
            }} 
          />

          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Full Name *</Label>
              <Input required value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Email (from account)</Label>
              <Input disabled value={user?.email || ""} />
            </div>
            <div className="space-y-2">
              <Label>Phone *</Label>
              <Input 
                value={phone} 
                onChange={e => {
                  setPhone(e.target.value);
                  if (missingFields.includes('phone')) setMissingFields(m => m.filter(f => f !== 'phone'));
                }} 
                placeholder="+1 234 567 8900" 
                className={missingFields.includes('phone') ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {missingFields.includes('phone') && <p className="text-xs text-red-500 mt-1">Phone number is required</p>}
            </div>
          </div>

          {/* Education */}
          <div className={`space-y-3 p-3 rounded-md border ${missingFields.includes('education') ? 'border-red-500 bg-red-50/10' : 'border-transparent'}`}>
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-zinc-900">Education *</h4>
              <Button type="button" variant="outline" size="sm" onClick={() => {
                setEducation([...education, { degree: "", institution: "", field_of_study: "" }]);
                if (missingFields.includes('education')) setMissingFields(m => m.filter(f => f !== 'education'));
              }}>
                <Plus className="h-4 w-4 mr-2" /> Add Education
              </Button>
            </div>
            {missingFields.includes('education') && <p className="text-xs text-red-500">At least one valid education entry is required.</p>}
            {education.map((edu, idx) => (
              <div key={idx} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start border p-3 rounded-md border-zinc-200 bg-zinc-50/50">
                <div className="md:col-span-3 space-y-1">
                  <Label className="text-xs">Degree</Label>
                  <Input placeholder="e.g. BS" value={edu.degree} onChange={e => { const n = [...education]; n[idx].degree = e.target.value; setEducation(n); }} />
                </div>
                <div className="md:col-span-4 space-y-1">
                  <Label className="text-xs">Institution</Label>
                  <Input placeholder="e.g. Stanford University" value={edu.institution} onChange={e => { const n = [...education]; n[idx].institution = e.target.value; setEducation(n); }} />
                </div>
                <div className="md:col-span-4 space-y-1">
                  <Label className="text-xs">Field of Study</Label>
                  <Input placeholder="e.g. Computer Science" value={edu.field_of_study} onChange={e => { const n = [...education]; n[idx].field_of_study = e.target.value; setEducation(n); }} />
                </div>
                <div className="md:col-span-1 pt-6 text-right">
                  <Button type="button" variant="ghost" size="icon" className="text-red-500 hover:text-red-700" onClick={() => setEducation(education.filter((_, i) => i !== idx))}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Work Experience */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-zinc-900">Work Experience</h4>
              <Button type="button" variant="outline" size="sm" onClick={() => setExperience([...experience, { role: "", company: "", duration: "" }])}>
                <Plus className="h-4 w-4 mr-2" /> Add Experience
              </Button>
            </div>
            {experience.map((exp, idx) => (
              <div key={idx} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start border p-3 rounded-md border-zinc-200 bg-zinc-50/50">
                <div className="md:col-span-4 space-y-1">
                  <Label className="text-xs">Role / Title</Label>
                  <Input placeholder="e.g. Software Engineer" value={exp.role} onChange={e => { const n = [...experience]; n[idx].role = e.target.value; setExperience(n); }} />
                </div>
                <div className="md:col-span-4 space-y-1">
                  <Label className="text-xs">Company</Label>
                  <Input placeholder="e.g. Acme Corp" value={exp.company} onChange={e => { const n = [...experience]; n[idx].company = e.target.value; setExperience(n); }} />
                </div>
                <div className="md:col-span-3 space-y-1">
                  <Label className="text-xs">Duration</Label>
                  <Input placeholder="e.g. 2020 - 2023" value={exp.duration} onChange={e => { const n = [...experience]; n[idx].duration = e.target.value; setExperience(n); }} />
                </div>
                <div className="md:col-span-1 pt-6 text-right">
                  <Button type="button" variant="ghost" size="icon" className="text-red-500 hover:text-red-700" onClick={() => setExperience(experience.filter((_, i) => i !== idx))}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Certifications */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-zinc-900">Certifications (Optional)</h4>
              <Button type="button" variant="outline" size="sm" onClick={() => setCertifications([...certifications, { name: "", issuing_body: "" }])}>
                <Plus className="h-4 w-4 mr-2" /> Add Certification
              </Button>
            </div>
            {certifications.map((cert, idx) => (
              <div key={idx} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start border p-3 rounded-md border-zinc-200 bg-zinc-50/50">
                <div className="md:col-span-6 space-y-1">
                  <Label className="text-xs">Certification Name</Label>
                  <Input placeholder="e.g. AWS Solutions Architect" value={cert.name} onChange={e => { const n = [...certifications]; n[idx].name = e.target.value; setCertifications(n); }} />
                </div>
                <div className="md:col-span-5 space-y-1">
                  <Label className="text-xs">Issuing Body</Label>
                  <Input placeholder="e.g. Amazon Web Services" value={cert.issuing_body} onChange={e => { const n = [...certifications]; n[idx].issuing_body = e.target.value; setCertifications(n); }} />
                </div>
                <div className="md:col-span-1 pt-6 text-right">
                  <Button type="button" variant="ghost" size="icon" className="text-red-500 hover:text-red-700" onClick={() => setCertifications(certifications.filter((_, i) => i !== idx))}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-4 gap-3">
            <Button variant="outline" type="button" onClick={onClose} disabled={isSubmitting}>Cancel</Button>
            <Button type="submit" className="bg-indigo-600 text-white hover:bg-indigo-700" disabled={isSubmitting}>
              {isSubmitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting...</> : "Submit Application"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function CandidateJobsPage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-64"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>}>
      <CandidateJobsContent />
    </Suspense>
  );
}
