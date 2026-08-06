"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Loader2, Upload, FileText, CheckCircle2, AlertCircle, UserCircle, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { components } from "@/lib/api/schema";

type ApplicationRead = components["schemas"]["ApplicationRead"];
type ResumeRead = components["schemas"]["ResumeRead"];
type CandidateRead = components["schemas"]["CandidateRead"];

export default function CandidateDashboard() {
  const [loading, setLoading] = useState(true);
  const [candidate, setCandidate] = useState<CandidateRead | null>(null);
  const [applications, setApplications] = useState<ApplicationRead[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [activeTab, setActiveTab] = useState<"overview" | "profile" | "notifications">("overview");
  const [updatingProfile, setUpdatingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const { data: candData, error: candErr } = await apiClient.GET("/api/v1/candidate-portal/me", {});
      if (candErr) throw candErr;
      setCandidate(candData as CandidateRead);

      try {
        const { data: appData } = await apiClient.GET("/api/v1/candidate-portal/applications", {});
        if (appData) {
          setApplications(appData as ApplicationRead[]);
        }
      } catch {
        // Silently ignore if they can't fetch it yet
      }

    } catch (err: any) {
      setError(err.message || "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !candidate) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/candidate-portal/resume`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) {
        throw new Error("Failed to upload resume");
      }
      
      alert("Resume uploaded successfully! It is now being parsed by our AI.");
    } catch (err: any) {
      alert(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleUpdateProfile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setUpdatingProfile(true);
    setProfileSuccess(false);

    const formData = new FormData(e.currentTarget);
    const name = formData.get("name") as string;
    const phone = formData.get("phone") as string;
    const bio = formData.get("bio") as string;

    try {
      const { data, error: updateErr } = await apiClient.PATCH("/api/v1/candidate-portal/profile", {
        body: {
          name: name || undefined,
          phone: phone || undefined,
          bio: bio || undefined
        }
      });
      if (updateErr) throw updateErr;
      setCandidate(data as CandidateRead);
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || "Failed to update profile");
    } finally {
      setUpdatingProfile(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-semibold text-zinc-900">Failed to load dashboard</h2>
        <p className="text-zinc-500 mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Welcome, {candidate.name}</h1>
        <p className="text-zinc-500 mt-1">Manage your applications and profile.</p>
      </div>

      <div className="flex border-b border-zinc-200">
        <button
          className={`py-3 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "overview" ? "border-indigo-600 text-indigo-600" : "border-transparent text-zinc-500 hover:text-zinc-700"
          }`}
          onClick={() => setActiveTab("overview")}
        >
          <div className="flex items-center gap-2"><FileText size={16}/> Overview</div>
        </button>
        <button
          className={`py-3 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "profile" ? "border-indigo-600 text-indigo-600" : "border-transparent text-zinc-500 hover:text-zinc-700"
          }`}
          onClick={() => setActiveTab("profile")}
        >
          <div className="flex items-center gap-2"><UserCircle size={16}/> Profile</div>
        </button>
        <button
          className={`py-3 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "notifications" ? "border-indigo-600 text-indigo-600" : "border-transparent text-zinc-500 hover:text-zinc-700"
          }`}
          onClick={() => setActiveTab("notifications")}
        >
          <div className="flex items-center gap-2"><Bell size={16}/> Notifications</div>
        </button>
      </div>

      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card className="shadow-md border-zinc-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-indigo-600" />
                Your Resume
              </CardTitle>
              <CardDescription>
                Upload your latest resume. Our AI will automatically parse it and match you with open roles.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-zinc-200 rounded-lg p-8 text-center bg-zinc-50 hover:bg-zinc-100 transition-colors">
                <Upload className="h-8 w-8 text-zinc-400 mx-auto mb-4" />
                <div className="mt-2 flex text-sm justify-center leading-6 text-zinc-600">
                  <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer rounded-md font-semibold text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 hover:text-indigo-500"
                  >
                    <span>Upload a file</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".pdf,.doc,.docx" onChange={handleFileUpload} disabled={uploading} />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs leading-5 text-zinc-500 mt-2">PDF, DOC, DOCX up to 10MB</p>
                
                {uploading && (
                  <div className="mt-4 flex items-center justify-center text-sm text-indigo-600 font-medium">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading and Parsing...
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-md border-zinc-200">
            <CardHeader>
              <CardTitle>Your Applications</CardTitle>
              <CardDescription>Track the status of roles you have applied for.</CardDescription>
            </CardHeader>
            <CardContent>
              {applications.length === 0 ? (
                <div className="text-center py-8 text-zinc-500 border rounded-lg bg-zinc-50">
                  You haven't applied to any jobs yet.
                </div>
              ) : (
                <ul className="space-y-4">
                  {applications.map(app => (
                    <li key={app.id} className="flex justify-between items-center p-4 border rounded-lg shadow-sm bg-white hover:border-indigo-200 transition-colors">
                      <div>
                        <p className="font-medium text-zinc-900 text-sm">Job ID: {app.job_id.slice(0, 8)}...</p>
                        <p className="text-xs text-zinc-500">Applied on {new Date(app.applied_at).toLocaleDateString()}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        <span className="text-sm font-medium capitalize text-emerald-700 bg-emerald-50 px-2 py-1 rounded-full border border-emerald-100">{app.status}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "profile" && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card className="max-w-2xl shadow-md border-zinc-200">
            <CardHeader>
              <CardTitle>Update Profile</CardTitle>
              <CardDescription>Make changes to your personal details.</CardDescription>
            </CardHeader>
            <form onSubmit={handleUpdateProfile}>
              <CardContent className="space-y-4">
                {profileSuccess && (
                  <div className="bg-emerald-50 text-emerald-700 p-3 rounded-md text-sm flex items-center gap-2 border border-emerald-100 mb-4">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>Profile updated successfully!</span>
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input id="name" name="name" defaultValue={candidate.name} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" defaultValue={candidate.email} disabled className="bg-zinc-100" />
                  <p className="text-xs text-zinc-500">Email cannot be changed.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input id="phone" name="phone" type="tel" defaultValue={candidate.phone || ""} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio / Description</Label>
                  <textarea 
                    id="bio" 
                    name="bio" 
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50" 
                    defaultValue={candidate.profile?.bio || ""}
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white" disabled={updatingProfile}>
                  {updatingProfile ? <><Loader2 className="mr-2 h-4 w-4 animate-spin"/> Saving...</> : "Save Changes"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {activeTab === "notifications" && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card className="shadow-md border-zinc-200">
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Recent updates and messages from recruiters.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-zinc-500 border rounded-lg border-dashed bg-zinc-50">
                <Bell className="h-8 w-8 mx-auto mb-3 text-zinc-300" />
                <p>You have no new notifications.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

    </div>
  );
}
