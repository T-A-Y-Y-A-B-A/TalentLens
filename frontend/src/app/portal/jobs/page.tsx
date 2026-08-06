"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Briefcase, MapPin, Building, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

type Job = {
  id: string;
  title: string;
  description: string;
  department?: { name: string } | null;
  created_at: string;
};

export default function CandidateJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [applyingTo, setApplyingTo] = useState<string | null>(null);
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function fetchJobs() {
      try {
        // Fetch global active jobs
        const { data, error } = await apiClient.GET("/api/v1/candidate-portal/jobs", {});
        if (data) {
          setJobs(data as unknown as Job[]);
        }
        
        // Also fetch candidate's applications to mark jobs as "Applied"
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
    }
    fetchJobs();
  }, []);

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
          description: "Your application has been successfully submitted. AI analysis is in progress.",
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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Job Board</h1>
        <p className="text-zinc-500 mt-2">Discover and apply to the latest opportunities.</p>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => {
            const isApplied = appliedJobs.has(job.id);
            return (
              <Card key={job.id} className="flex flex-col transition-all hover:shadow-md">
                <CardHeader>
                  <CardTitle className="line-clamp-1">{job.title}</CardTitle>
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
                </CardHeader>
                <CardContent className="flex-1">
                  <p className="text-sm text-zinc-600 line-clamp-3">
                    {job.description}
                  </p>
                </CardContent>
                <CardFooter>
                  <Button 
                    className={`w-full ${isApplied ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' : 'bg-indigo-600 hover:bg-indigo-700 text-white'}`}
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
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
