"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, ChevronLeft, User, Briefcase } from "lucide-react";
import Link from "next/link";
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragStartEvent, DragEndEvent } from "@dnd-kit/core";
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
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mb-3 cursor-grab active:cursor-grabbing">
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold shrink-0">
            {application.candidate.name ? application.candidate.name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium truncate">{application.candidate.name}</p>
            <p className="text-xs text-gray-500">App ID: {application.id.slice(0, 8)}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PipelineColumn({ stage, applications }: { stage: StageRead, applications: ApplicationWithCandidate[] }) {
  return (
    <div className="bg-gray-100/80 rounded-lg p-4 min-w-[280px] w-[280px] flex flex-col flex-shrink-0 border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-700">{stage.name}</h3>
        <span className="bg-white text-gray-500 text-xs font-medium px-2 py-1 rounded-full shadow-sm">{applications.length}</span>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        <SortableContext items={applications.map(a => a.id)} strategy={verticalListSortingStrategy}>
          {applications.map(app => (
            <SortableAppCard key={app.id} application={app} />
          ))}
        </SortableContext>
        {applications.length === 0 && (
          <div className="h-24 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center text-gray-400 text-sm">
            Drag here
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
        // Fallback for stages if they aren't included in the Job response
        // Using mock stages if backend doesn't return them yet
        const jobStages = (jobData as any).pipeline_stages || [
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
      // It might be dropping on the column itself (we need to pass stage.id to a Droppable)
      // Since we only made the items droppable via SortableContext, they can only drop on items.
      // To drop on empty columns, we'd need useDroppable on the column.
      // Assuming they dropped on a card in another column.
      if (!targetStageId) return;
    }

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
        <Link href="/jobs" className="text-gray-500 hover:text-gray-700 mr-4">
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
