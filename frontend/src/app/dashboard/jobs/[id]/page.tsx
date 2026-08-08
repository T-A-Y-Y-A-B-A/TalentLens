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
      <div className="mb-6 flex items-center">
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

      {/* Pipeline Kanban Board */}
      <div className="flex-1 overflow-x-auto">
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
      </div>
    </div>
  );
}
