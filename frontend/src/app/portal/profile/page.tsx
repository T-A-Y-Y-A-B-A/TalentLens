"use client";

import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { Loader2, UploadCloud, FileText, CheckCircle, GraduationCap, Briefcase, Award, Trash2 } from "lucide-react";
import { toast } from "sonner";

type ParsedData = {
  skills: string[];
  experience: any[];
  education: any[];
  certifications: any[];
  projects: any[];
};

type CandidateProfile = {
  name: string;
  email: string;
  parsed_data?: ParsedData | null;
  resume?: {
    file_url: string;
  } | null;
};

export default function CandidateProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [isStuck, setIsStuck] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Delete account state
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const { data, error } = await apiClient.GET("/api/v1/candidate-portal/me", {});
      if (data) {
        setProfile(data as unknown as CandidateProfile);
      }
    } catch (err) {
      console.error("Failed to fetch profile", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let stuckTimeout: NodeJS.Timeout;

    if (profile?.resume && !profile?.parsed_data) {
      // Start polling every 5 seconds
      interval = setInterval(() => {
        fetchProfile();
      }, 5000);

      // Show warning after 45 seconds if still analyzing
      stuckTimeout = setTimeout(() => {
        setIsStuck(true);
      }, 45000);
    } else {
      setIsStuck(false);
    }

    return () => {
      if (interval) clearInterval(interval);
      if (stuckTimeout) clearTimeout(stuckTimeout);
    };
  }, [profile?.resume, profile?.parsed_data]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf" && !file.name.endsWith(".docx")) {
      toast.error("Invalid File", {
        description: "Please upload a .pdf or .docx file."
      });
      return;
    }

    setUploading(true);
    try {
      // Need to use native fetch for FormData since openapi-fetch sometimes struggles with it
      const formData = new FormData();
      formData.append("file", file);

      const token = localStorage.getItem("access_token");
      const response = await fetch("/api/v1/candidate-portal/resume", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error("Failed to upload");
      }

      toast.success("Resume Uploaded", {
        description: "Your resume is now being analyzed by our AI. Check back in a few minutes.",
      });
      
      // Refresh after a delay to potentially get parsed data
      setTimeout(fetchProfile, 5000);
    } catch (err: any) {
      toast.error("Upload Error", {
        description: "An error occurred while uploading your resume."
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDeleteAccount = async () => {
    setDeletingAccount(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/candidate-portal/me", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        // Clear all local state and do a hard redirect so no stale session data remains
        localStorage.removeItem("access_token");
        window.location.href = "/portal/login";
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error("Delete Failed", { description: err?.detail ?? "Could not delete account." });
        setDeleteOpen(false);
      }
    } catch {
      toast.error("Delete Failed", { description: "An error occurred. Please try again." });
      setDeleteOpen(false);
    } finally {
      setDeletingAccount(false);
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
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">My Profile</h1>
        <p className="text-zinc-500 mt-2">Manage your resume and AI-extracted profile.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Column */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm font-medium text-zinc-900">{profile?.name}</p>
                <p className="text-sm text-zinc-500">{profile?.email}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resume Upload</CardTitle>
              <CardDescription>Upload your latest resume to automatically update your profile.</CardDescription>
            </CardHeader>
            <CardContent>
              <div 
                className={`border-2 border-dashed border-zinc-200 rounded-xl p-8 text-center transition-colors ${!profile?.resume && !uploading ? 'hover:bg-zinc-50 cursor-pointer' : ''}`}
                onClick={() => {
                  if (!profile?.resume && !uploading) {
                    fileInputRef.current?.click();
                  }
                }}
              >
                {uploading ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="h-10 w-10 text-indigo-600 animate-spin mb-4" />
                    <p className="text-sm font-medium text-zinc-900">Uploading...</p>
                  </div>
                ) : profile?.resume ? (
                  <div className="flex flex-col items-center">
                    <div className="h-12 w-12 bg-green-50 rounded-full flex items-center justify-center mb-4">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <p className="text-lg font-medium text-zinc-900 mb-4">Resume Uploaded</p>
                    <div className="flex flex-col gap-3 w-full max-w-[220px]">
                      <Button 
                        variant="outline" 
                        className="w-full"
                        onClick={(e) => {
                          e.stopPropagation();
                          const token = localStorage.getItem("access_token");
                          const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/candidate-portal/resume/download`;
                          fetch(downloadUrl, { headers: { "Authorization": `Bearer ${token}` } })
                            .then(async res => {
                              if (!res.ok) throw new Error("Failed to download");
                              const blob = await res.blob();
                              const url = window.URL.createObjectURL(blob);
                              window.open(url, "_blank");
                              setTimeout(() => window.URL.revokeObjectURL(url), 5000);
                            })
                            .catch(() => toast.error("Failed to download resume"));
                        }}
                      >
                        <FileText className="mr-2 h-4 w-4" /> View PDF
                      </Button>
                      <Button 
                        className="w-full"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                      >
                        <UploadCloud className="mr-2 h-4 w-4" /> Update Resume
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="h-12 w-12 bg-indigo-50 rounded-full flex items-center justify-center mb-4">
                      <UploadCloud className="h-6 w-6 text-indigo-600" />
                    </div>
                    <p className="text-sm font-medium text-zinc-900 mb-1">Click to upload</p>
                    <p className="text-xs text-zinc-500">PDF or DOCX up to 5MB</p>
                  </div>
                )}
              </div>
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".pdf,.docx" 
                onChange={handleFileUpload} 
              />
            </CardContent>
          </Card>
        </div>

        {/* Parsed Data Column */}
        <div className="lg:col-span-2 space-y-6">
          {!profile?.parsed_data ? (
            <Card className="h-full min-h-[400px] flex items-center justify-center bg-zinc-50/50 border-dashed">
              <div className="text-center p-8 max-w-sm">
                {profile?.resume ? (
                  <>
                    <Loader2 className="h-12 w-12 text-indigo-600 animate-spin mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-zinc-900">Analyzing Resume...</h3>
                    <p className="text-zinc-500 mt-2 text-sm">Our AI is extracting your skills and experience. This usually takes 1-2 minutes.</p>
                    
                    {isStuck && (
                      <div className="mt-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
                        <p className="text-amber-800 text-sm font-medium mb-3 text-left">
                          This is taking longer than usual. There might be a processing delay or an internet issue.
                        </p>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="bg-white w-full border-amber-200 hover:bg-amber-100 text-amber-900"
                          onClick={() => {
                            setIsStuck(false);
                            fetchProfile();
                          }}
                        >
                          Retry Now
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <FileText className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-zinc-900">No Profile Data Yet</h3>
                    <p className="text-zinc-500 mt-2 text-sm">Upload your resume and our AI will automatically extract your skills and experience.</p>
                  </>
                )}
              </div>
            </Card>
          ) : (
            <>
              {/* Skills */}
              <Card>
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-5 w-5 text-indigo-600" />
                    Top Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {profile.parsed_data.skills.map((skill, i) => (
                      <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {skill}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Experience */}
              <Card>
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-indigo-600" />
                    Experience
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {profile.parsed_data.experience.map((exp, i) => (
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
                </CardContent>
              </Card>
              
              {/* Education */}
              <Card>
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2">
                    <GraduationCap className="h-5 w-5 text-indigo-600" />
                    Education
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {profile.parsed_data.education.map((edu, i) => (
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
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>

      {/* Danger Zone — Delete Account */}
      <Card className="border-red-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-red-700 flex items-center gap-2 text-base">
            <Trash2 className="h-4 w-4" />
            Danger Zone
          </CardTitle>
          <CardDescription className="text-red-600/80">
            Permanently delete your account and all associated data. This cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            id="delete-account-btn"
            variant="outline"
            className="border-red-300 text-red-700 hover:bg-red-50 hover:text-red-800"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete My Account
          </Button>
        </CardContent>
      </Card>

      {/* Delete Account Confirmation Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={(open) => !open && !deletingAccount && setDeleteOpen(false)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-red-700">Delete Your Account</AlertDialogTitle>
            <AlertDialogDescription>
              This will <strong>permanently soft-delete</strong> your account and withdraw all your active
              job applications. You will be immediately logged out.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 py-2 text-sm text-zinc-600">
            <p className="bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-amber-800 font-medium">
              ⚠ You will not be able to recover your account or applications after this action.
            </p>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deletingAccount}>Keep My Account</AlertDialogCancel>
            <AlertDialogAction
              id="confirm-delete-account-btn"
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={handleDeleteAccount}
              disabled={deletingAccount}
            >
              {deletingAccount && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Yes, Delete My Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
