"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, ChevronLeft, User, Briefcase } from "lucide-react";
import Link from "next/link";
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragStartEvent, DragEndEvent, useDroppable } from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { components } from "@/lib/api/schema";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { JobMatches } from "@/components/JobMatches";
import { Sparkles, Edit } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LocationSelect } from "@/components/LocationSelect";

type JobRead = components["schemas"]["JobRead"];
type StageRead = components["schemas"]["PipelineStageRead"];
type ApplicationRead = components["schemas"]["ApplicationRead"];
type CandidateRead = components["schemas"]["CandidateRead"];

// Extend Application to include candidate details for rendering
interface ApplicationWithCandidate extends ApplicationRead {
  candidate: CandidateRead;
}

function SortableAppCard({ application }: { application: ApplicationWithCandidate }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: application.id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mb-3">
      <div className={`bg-white p-3 rounded-lg shadow-sm border space-y-2 cursor-grab active:cursor-grabbing transition-colors ${isDragging ? 'border-indigo-400 shadow-md scale-105 relative z-10' : 'border-zinc-200 hover:border-indigo-300'}`}>
        <p className="font-bold text-zinc-900 text-sm">{application.candidate.name || "Unknown Candidate"}</p>
        <p className="text-xs text-zinc-500">App ID: {application.id.slice(0, 8)}</p>
      </div>
    </div>
  );
}

function PipelineColumn({ stage, applications }: { stage: StageRead, applications: ApplicationWithCandidate[] }) {
  const { setNodeRef, isOver } = useDroppable({
    id: stage.id,
    data: {
      type: "Column",
      stage
    }
  });

  return (
    <div ref={setNodeRef} className={`bg-zinc-50 rounded-xl p-3 space-y-3 border ${isOver ? 'border-indigo-300 bg-indigo-50/30' : 'border-zinc-100'} min-w-[320px] w-[320px] flex flex-col flex-shrink-0 transition-colors`}>
      <div className="flex justify-between items-center px-1">
        <h3 className="text-sm font-bold text-zinc-700 uppercase tracking-wide">{stage.name}</h3>
        <span className="bg-zinc-200 text-zinc-600 text-xs px-2 py-0.5 rounded-full font-bold shadow-sm">{applications.length}</span>
      </div>
      
      <div className="flex-1 overflow-y-auto min-h-[150px]">
        <SortableContext items={applications.map(a => a.id)} strategy={verticalListSortingStrategy}>
          {applications.map(app => (
            <SortableAppCard key={app.id} application={app} />
          ))}
        </SortableContext>
        {applications.length === 0 && (
          <div className="border-2 border-dashed border-zinc-200 rounded-lg h-24 flex items-center justify-center pointer-events-none">
            <p className="text-xs text-zinc-400 font-medium">Drop candidate here</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function JobPipelineBoard() {
  const params = useParams();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<JobRead | null>(null);
  const [stages, setStages] = useState<StageRead[]>([]);
  const [applications, setApplications] = useState<ApplicationWithCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dnd state
  const [activeId, setActiveId] = useState<string | null>(null);

  // Edit Job state
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editRequiredSkills, setEditRequiredSkills] = useState("");
  const [editExperienceYears, setEditExperienceYears] = useState("");
  const [editEducation, setEditEducation] = useState("");
  const [editWorkType, setEditWorkType] = useState<string>("REMOTE");
  const [editLocation, setEditLocation] = useState("");
  const [editSalaryRange, setEditSalaryRange] = useState("");
  const [editCompanyDescription, setEditCompanyDescription] = useState("");
  const [editKeyResponsibilities, setEditKeyResponsibilities] = useState("");
  const [editExpectations, setEditExpectations] = useState("");
  const [editBenefits, setEditBenefits] = useState("");
  const [roughNotes, setRoughNotes] = useState("");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (job) {
      setEditTitle(job.title || "");
      setEditDescription(job.description || "");
      setEditWorkType(job.work_type || "REMOTE");
      setEditLocation(job.location || "");
      setEditSalaryRange((job as any).salary_range || "");
      setEditCompanyDescription((job as any).company_description || "");
      setEditKeyResponsibilities(Array.isArray((job as any).key_responsibilities) ? (job as any).key_responsibilities.join("\n") : "");
      setEditExpectations(Array.isArray((job as any).expectations) ? (job as any).expectations.join("\n") : "");
      setEditBenefits(Array.isArray((job as any).benefits) ? (job as any).benefits.join("\n") : "");
      const reqs = (job as any).requirements;
      if (reqs) {
        setEditRequiredSkills(reqs.required_skills?.join(", ") || "");
        setEditExperienceYears(reqs.experience_years?.toString() || "");
        setEditEducation(reqs.education || "");
      }
    }
  }, [job]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Job Details
        const { data: jobData, error: jobErr } = await apiClient.GET("/api/v1/jobs/{job_id}", {
          params: { path: { job_id: jobId } }
        });
        if (jobErr) throw jobErr;
        setJob(jobData as any);
        // Fallback for stages if they aren't included in the Job response or are empty
        // Using mock stages if backend doesn't return them yet
        const jobStages = ((jobData as any).pipeline_stages && (jobData as any).pipeline_stages.length > 0) 
          ? (jobData as any).pipeline_stages 
          : [
              { id: "stage-1", name: "Sourced", order_index: 0 },
              { id: "stage-2", name: "Applied", order_index: 1 },
              { id: "stage-3", name: "Interviewing", order_index: 2 },
              { id: "stage-4", name: "Offered", order_index: 3 },
              { id: "stage-5", name: "Hired", order_index: 4 },
            ];
        // Ensure stages are sorted by order
        jobStages.sort((a: any, b: any) => (a.order_index || 0) - (b.order_index || 0));
        setStages(jobStages);

        // Fetch Applications for this Job
        const { data: appData, error: appErr } = await apiClient.GET("/api/v1/applications", {
          params: { query: { job_id: jobId } }
        });
        if (appErr) throw appErr;
        
        // Fetch candidates for these applications to display names
        const apps = (appData as any as ApplicationRead[]) || [];
        const enrichedApps: ApplicationWithCandidate[] = [];
        
        for (const app of apps) {
          const { data: candData } = await apiClient.GET("/api/v1/candidates/{candidate_id}", {
            params: { path: { candidate_id: app.candidate_id } }
          });
          if (candData) {
            enrichedApps.push({ ...app, candidate: candData as CandidateRead });
          } else {
            // fallback if candidate not found
            enrichedApps.push({ ...app, candidate: { id: app.candidate_id, name: "Unknown", email: "", created_at: new Date().toISOString(), updated_at: new Date().toISOString() } as components["schemas"]["CandidateRead"] });
          }
        }
        
        setApplications(enrichedApps);

      } catch (err: any) {
        setError(err.message || "Failed to load pipeline data");
      } finally {
        setLoading(false);
      }
    };

    if (jobId) {
      fetchData();
    }
  }, [jobId]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    
    if (!over) return;

    const appId = active.id as string;
    
    // Find what stage the user dragged over
    // If they dragged over another card, `over.id` is an appId.
    // If they dragged over an empty column, `over.id` is a stageId (wait, we need to handle dropping on empty column)
    
    // For simplicity, let's figure out which column the `over` item belongs to
    let targetStageId = "";
    
    // Check if dragged over another application card
    const overApp = applications.find(a => a.id === over.id);
    if (overApp && overApp.current_stage_id) {
      targetStageId = overApp.current_stage_id;
    } else {
      // Check if dropped directly onto an empty column
      const overStage = stages.find(s => s.id === over.id);
      if (overStage) {
        targetStageId = overStage.id;
      }
    }

    if (!targetStageId) return;

    const activeApp = applications.find(a => a.id === appId);
    if (!activeApp || activeApp.current_stage_id === targetStageId) return;

    // 1. Optimistic UI Update
    const previousApplications = [...applications];
    setApplications(apps => apps.map(app => 
      app.id === appId ? { ...app, current_stage_id: targetStageId } : app
    ));

    try {
      const { error } = await apiClient.PATCH("/api/v1/applications/{application_id}/stage", {
        params: { path: { application_id: appId } },
        body: { to_stage_id: targetStageId }
      });

      if (error) {
        throw new Error((error as any).detail || "Failed to update stage");
      }
    } catch (err: any) {
      // 2. Rollback on failure (e.g. RBAC error)
      alert(`Could not move candidate: ${err.message}`);
      setApplications(previousApplications);
    }
  };

  const handleEnhanceWithAI = async () => {
    if (!roughNotes.trim()) return;
    setIsEnhancing(true);
    try {
      const { data, error: enhanceError } = await apiClient.POST("/api/v1/jobs/enhance", {
        body: {
          rough_notes: roughNotes,
        },
      });
      if (enhanceError) {
        alert("Failed to enhance job details");
      } else if (data) {
        if (data.title) setEditTitle(data.title);
        if (data.description) setEditDescription(data.description);
        if (data.salary_range) setEditSalaryRange(data.salary_range);
        if (data.company_description) setEditCompanyDescription(data.company_description);
        if (data.key_responsibilities && Array.isArray(data.key_responsibilities)) {
          setEditKeyResponsibilities(data.key_responsibilities.join("\n"));
        }
        if (data.expectations && Array.isArray(data.expectations)) {
          setEditExpectations(data.expectations.join("\n"));
        }
        if (data.benefits && Array.isArray(data.benefits)) {
          setEditBenefits(data.benefits.join("\n"));
        }
      }
    } catch {
      alert("Error enhancing job details");
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleUpdateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdating(true);
    try {
      const parsedSkills = editRequiredSkills
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
        
      const parsedExp = editExperienceYears ? parseInt(editExperienceYears, 10) : null;

      const parsedKeyResponsibilities = editKeyResponsibilities
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const parsedExpectations = editExpectations
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const parsedBenefits = editBenefits
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const { data, error: updateError } = await apiClient.PATCH("/api/v1/jobs/{job_id}", {
        params: { path: { job_id: jobId } },
        body: {
          title: editTitle,
          description: editDescription,
          work_type: editWorkType as any,
          location: editLocation || null,
          salary_range: editSalaryRange || null,
          company_description: editCompanyDescription || null,
          key_responsibilities: parsedKeyResponsibilities.length > 0 ? parsedKeyResponsibilities : null,
          expectations: parsedExpectations.length > 0 ? parsedExpectations : null,
          benefits: parsedBenefits.length > 0 ? parsedBenefits : null,
          requirements: {
            required_skills: parsedSkills,
            experience_years: parsedExp,
            education: editEducation || null,
          }
        }
      });
      if (updateError) {
        alert("Failed to update job: " + JSON.stringify(updateError));
      } else if (data) {
        setJob(data as any);
        alert("Job updated successfully");
      }
    } catch (err: any) {
      alert("Error updating job");
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-10rem)]">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="text-center py-8 text-red-500">
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        <p>{error || "Job not found"}</p>
      </div>
    );
  }

  const activeApplication = activeId ? applications.find(a => a.id === activeId) : null;

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/dashboard/jobs" className="text-gray-500 hover:text-gray-700 mr-4">
            <ChevronLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2">
              <Briefcase className="h-6 w-6 text-indigo-600" />
              {job.title}
            </h1>
            <p className="text-sm text-gray-500 capitalize">{job.status} Role</p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="pipeline" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mb-6 self-start">
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="matches" className="flex items-center gap-2">
             <Sparkles size={14} className="text-indigo-500" /> AI Matches
          </TabsTrigger>
          <TabsTrigger value="edit" className="flex items-center gap-2">
             <Edit size={14} /> Edit
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="pipeline" className="flex-1 overflow-x-auto m-0 p-0 focus-visible:outline-none">
          <DndContext sensors={sensors} collisionDetection={closestCorners} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="flex gap-4 h-full pb-4">
              {stages.map(stage => (
                <PipelineColumn 
                  key={stage.id} 
                  stage={stage} 
                  applications={applications.filter(a => a.current_stage_id === stage.id)} 
                />
              ))}
            </div>

            <DragOverlay>
              {activeApplication ? <SortableAppCard application={activeApplication} /> : null}
            </DragOverlay>
          </DndContext>
        </TabsContent>

        <TabsContent value="matches" className="flex-1 overflow-y-auto m-0 p-0 pr-4 focus-visible:outline-none">
          <JobMatches jobId={jobId} />
        </TabsContent>

        <TabsContent value="edit" className="flex-1 overflow-y-auto m-0 p-0 pr-4 focus-visible:outline-none">
          <Card className="max-w-3xl border shadow-sm">
            <CardHeader>
              <CardTitle>Edit Job Details</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateJob} className="space-y-6">
                {/* AI Enhancement Section */}
                <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-4 space-y-3 mb-6">
                  <div className="flex items-center gap-2 text-sm font-semibold text-indigo-900">
                    <Sparkles className="h-4 w-4 text-indigo-600" />
                    <span>Enhance with AI</span>
                  </div>
                  <p className="text-xs text-indigo-700">
                    Paste or write rough notes about the role below. AI will automatically draft structured job details, responsibilities, expectations, and benefits.
                  </p>
                  <Textarea
                    id="roughNotes"
                    value={roughNotes}
                    onChange={(e) => setRoughNotes(e.target.value)}
                    placeholder="e.g. Senior Frontend Dev, React + TS, 5y exp, remote, $120k-$150k, leading team, code reviews, full health & 401k..."
                    rows={3}
                    className="bg-white text-sm"
                  />
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      size="sm"
                      variant="default"
                      className="bg-indigo-600 hover:bg-indigo-700 text-white"
                      onClick={handleEnhanceWithAI}
                      disabled={isEnhancing || !roughNotes.trim()}
                    >
                      {isEnhancing ? (
                        <>
                          <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                          Enhancing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-3.5 w-3.5" />
                          Enhance with AI
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="editTitle">Job Title</Label>
                  <Input 
                    id="editTitle" 
                    value={editTitle} 
                    onChange={(e) => setEditTitle(e.target.value)} 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editDescription">Job Description</Label>
                  <Textarea 
                    id="editDescription" 
                    value={editDescription} 
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={3}
                    required 
                  />
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="editSalaryRange">Salary Range</Label>
                    <Input 
                      id="editSalaryRange" 
                      value={editSalaryRange} 
                      onChange={(e) => setEditSalaryRange(e.target.value)} 
                      placeholder="e.g. $120,000 - $150,000 / year" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="editCompanyDescription">Company Description</Label>
                    <Input 
                      id="editCompanyDescription" 
                      value={editCompanyDescription} 
                      onChange={(e) => setEditCompanyDescription(e.target.value)} 
                      placeholder="e.g. Fast-growing AI enterprise startup" 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Location</Label>
                    <LocationSelect value={editLocation} onChange={setEditLocation} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="editWorkType">Work Type</Label>
                    <Select value={editWorkType} onValueChange={(val) => val && setEditWorkType(val)} required>
                      <SelectTrigger id="editWorkType"><SelectValue placeholder="Select work type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="REMOTE">Remote</SelectItem>
                        <SelectItem value="ONSITE">Onsite</SelectItem>
                        <SelectItem value="HYBRID">Hybrid</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="space-y-4 pt-4 border-t">
                  <h3 className="text-sm font-semibold">Requirements</h3>
                  
                  <div className="space-y-2">
                    <Label htmlFor="editRequiredSkills">Required Skills (comma-separated)</Label>
                    <Input 
                      id="editRequiredSkills" 
                      value={editRequiredSkills} 
                      onChange={(e) => setEditRequiredSkills(e.target.value)} 
                      placeholder="Python, React, TypeScript..." 
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="editExperienceYears">Experience (Years)</Label>
                      <Input 
                        id="editExperienceYears" 
                        type="number"
                        min="0"
                        value={editExperienceYears} 
                        onChange={(e) => setEditExperienceYears(e.target.value)} 
                        placeholder="e.g. 3" 
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="editEducation">Education</Label>
                      <Input 
                        id="editEducation" 
                        value={editEducation} 
                        onChange={(e) => setEditEducation(e.target.value)} 
                        placeholder="e.g. Bachelor's in CS" 
                      />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2 pt-4 border-t">
                  <Label htmlFor="editKeyResponsibilities">Key Responsibilities (one per line)</Label>
                  <Textarea
                    id="editKeyResponsibilities"
                    value={editKeyResponsibilities}
                    onChange={(e) => setEditKeyResponsibilities(e.target.value)}
                    placeholder="Architect robust web applications&#10;Mentor junior developers&#10;Lead sprint planning"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editExpectations">Expectations / Goals (one per line)</Label>
                  <Textarea
                    id="editExpectations"
                    value={editExpectations}
                    onChange={(e) => setEditExpectations(e.target.value)}
                    placeholder="Deliver MVP features within Q1&#10;Maintain 99.9% uptime SLA"
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editBenefits">Benefits & Perks (one per line)</Label>
                  <Textarea
                    id="editBenefits"
                    value={editBenefits}
                    onChange={(e) => setEditBenefits(e.target.value)}
                    placeholder="Comprehensive Health, Dental, Vision&#10;401(k) matching up to 4%&#10;Unlimited PTO"
                    rows={2}
                  />
                </div>
                
                <div className="pt-4 flex justify-end">
                  <Button type="submit" disabled={updating}>
                    {updating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save Changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
