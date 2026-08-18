"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Plus, Briefcase, Trash2 } from "lucide-react";
import Link from "next/link";
import { components } from "@/lib/api/schema";
import { LocationSelect } from "@/components/LocationSelect";

type JobRead = components["schemas"]["JobRead"];

export default function JobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog & Form State
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [education, setEducation] = useState("");
  const [workType, setWorkType] = useState<string>("REMOTE");
  const [location, setLocation] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<JobRead | null>(null);
  const [deleting, setDeleting] = useState(false);

  const canDelete = user?.role === "hr_manager" || user?.role === "super_admin";

  const fetchJobs = async () => {
    try {
      const { data, error } = await apiClient.GET("/api/v1/jobs", {});
      if (error) {
        setError(error as any);
      } else if (data) {
        setJobs(data);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const parsedSkills = requiredSkills
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
        
      const parsedExp = experienceYears ? parseInt(experienceYears, 10) : null;

      const { data, error: createError } = await apiClient.POST("/api/v1/jobs", {
        body: {
          title,
          description,
          status: "open",
          work_type: workType as any,
          requirements: {
            required_skills: parsedSkills,
            experience_years: parsedExp,
            education: education || null,
          }
        }
      });
      if (createError) {
        alert("Failed to create job");
      } else if (data) {
        setJobs([data, ...jobs]);
        setOpen(false);
        setTitle("");
        setDescription("");
        setRequiredSkills("");
        setExperienceYears("");
        setEducation("");
        setLocation("");
      }
    } catch (err: any) {
      alert("Error creating job");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteJob = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/jobs/${deleteTarget.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setJobs((prev) => prev.filter((j) => j.id !== deleteTarget.id));
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err?.detail ?? "Failed to delete job");
      }
    } catch {
      alert("Error deleting job");
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Jobs</h1>
          <p className="text-sm text-gray-500">Manage open roles and recruitment pipelines.</p>
        </div>
        
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Job
            </Button>
          } />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Job</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateJob} className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="title">Job Title</Label>
                <Input 
                  id="title" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)} 
                  placeholder="e.g. Senior Frontend Engineer" 
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Job Description</Label>
                <Input 
                  id="description" 
                  value={description} 
                  onChange={(e) => setDescription(e.target.value)} 
                  placeholder="Brief overview of the role..." 
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="requiredSkills">Required Skills (comma-separated)</Label>
                <Input 
                  id="requiredSkills" 
                  value={requiredSkills} 
                  onChange={(e) => setRequiredSkills(e.target.value)} 
                  placeholder="Python, React, TypeScript..." 
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Location</Label>
                  <LocationSelect value={location} onChange={setLocation} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="workType">Work Type</Label>
                  <Select value={workType} onValueChange={(val) => val && setWorkType(val)} required>
                    <SelectTrigger id="workType"><SelectValue placeholder="Select work type" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="REMOTE">Remote</SelectItem>
                      <SelectItem value="ONSITE">Onsite</SelectItem>
                      <SelectItem value="HYBRID">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="experienceYears">Experience (Years)</Label>
                  <Input 
                    id="experienceYears" 
                    type="number"
                    min="0"
                    value={experienceYears} 
                    onChange={(e) => setExperienceYears(e.target.value)} 
                    placeholder="e.g. 3" 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="education">Education</Label>
                  <Input 
                    id="education" 
                    value={education} 
                    onChange={(e) => setEducation(e.target.value)} 
                    placeholder="e.g. Bachelor's in CS" 
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Job
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Postings</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">
              {typeof error === "string" ? error : "An error occurred while fetching jobs."}
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12 flex flex-col items-center">
              <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                <Briefcase className="h-6 w-6 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">No jobs found</h3>
              <p className="text-gray-500 mb-4 text-sm">Get started by creating a new job posting.</p>
              <Button variant="outline" onClick={() => setOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Job
              </Button>
            </div>
          ) : (
            <div className="border rounded-md">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium">
                        <Link href={`/dashboard/jobs/${job.id}`} className="text-indigo-600 hover:underline">
                          {job.title}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          job.status === "open" ? "bg-green-100 text-green-800" :
                          job.status === "draft" ? "bg-gray-100 text-gray-800" :
                          "bg-yellow-100 text-yellow-800"
                        }`}>
                          {job.status}
                        </span>
                      </TableCell>
                    <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`/dashboard/jobs/${job.id}`}>
                            <Button variant="ghost" size="sm">View Pipeline</Button>
                          </Link>
                          {canDelete && (
                            <Button
                              id={`delete-job-${job.id}`}
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => setDeleteTarget(job)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Job Confirmation Dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Job Posting</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <span className="font-semibold">{deleteTarget?.title}</span>?
              This will soft-delete the job and it will no longer appear in the pipeline.
              This action cannot be undone via the UI.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              id="confirm-delete-job-btn"
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={handleDeleteJob}
              disabled={deleting}
            >
              {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete Job
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
