"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function ScheduleInterviewPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [interviewers, setInterviewers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [applicationId, setApplicationId] = useState("");
  const [interviewerId, setInterviewerId] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState("60");
  const [meetingLink, setMeetingLink] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      if (authLoading) return;
      if (!user) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const token = localStorage.getItem("access_token");
        const headers = { Authorization: `Bearer ${token}` };
        
        // Fetch candidates (applications)
        const appsRes = await fetch(`${API_BASE}/api/v1/applications`, { headers });
        if (appsRes.ok) {
          const data = await appsRes.json();
          setCandidates(data);
        }

        // Fetch interviewers (org users)
        if (user.org_id) {
          const usersRes = await fetch(`${API_BASE}/api/v1/organizations/${user.org_id}/users`, { headers });
          if (usersRes.ok) {
            const data = await usersRes.json();
            setInterviewers(data);
          }
        }
      } catch (err) {
        console.error("Error fetching form data", err);
        setError("Failed to load applications or interviewers. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    
    try {
      const scheduled_at = `${date}T${time}:00Z`;
      const token = localStorage.getItem("access_token");
      
      const payload = {
        application_id: applicationId,
        interviewer_id: interviewerId,
        scheduled_at,
        duration_minutes: parseInt(duration),
        meeting_link: meetingLink || null,
        notes: notes || null
      };

      const res = await fetch(`${API_BASE}/api/v1/interviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const selectedApp = candidates.find(c => c.id === applicationId);
        const jobId = selectedApp?.job_id || selectedApp?.job?.id;
        if (jobId) {
          router.push(`/dashboard/jobs/${jobId}`);
        } else {
          router.push("/dashboard/interviews");
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData?.detail || errData?.message || "Failed to schedule interview.");
      }
    } catch (err) {
      console.error("Interview submission error", err);
      setError("Network error submitting interview. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/interviews" className={buttonVariants({ variant: "ghost", size: "icon", className: "rounded-full" })}>
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Schedule Interview</h1>
          <p className="text-gray-500 mt-1">Set up a new interview with a candidate.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Interview Details</CardTitle>
            <CardDescription>Select the candidate and interviewer, and choose a time.</CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="grid gap-2">
              <Label htmlFor="candidate">Candidate</Label>
              <select
                id="candidate"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
                value={applicationId}
                onChange={(e) => setApplicationId(e.target.value)}
                disabled={loading}
              >
                <option value="" disabled>Select a candidate</option>
                {candidates.map((c) => {
                  const candidateName = c.candidate?.name || c.candidate_name || "Applicant";
                  const jobTitle = c.job?.title || c.job_title || "Position";
                  return (
                    <option key={c.id} value={c.id}>
                      {candidateName} - {jobTitle}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="interviewer">Interviewer</Label>
              <select
                id="interviewer"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
                value={interviewerId}
                onChange={(e) => setInterviewerId(e.target.value)}
                disabled={loading}
              >
                <option value="" disabled>Select an interviewer</option>
                {interviewers.map((i) => {
                  const name = i.full_name || (i.email ? i.email.split("@")[0] : "Member");
                  const roleFormatted = i.role ? i.role.replace("_", " ") : "";
                  return (
                    <option key={i.id} value={i.id}>
                      {name} ({roleFormatted})
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="date">Date</Label>
                <Input type="date" id="date" required value={date} onChange={(e) => setDate(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="time">Time</Label>
                <Input type="time" id="time" required value={time} onChange={(e) => setTime(e.target.value)} />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="duration">Duration</Label>
              <select
                id="duration"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              >
                <option value="30">30 minutes</option>
                <option value="45">45 minutes</option>
                <option value="60">60 minutes (1 hour)</option>
                <option value="90">90 minutes (1.5 hours)</option>
              </select>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="meeting_link">Meeting Link (Optional)</Label>
              <Input 
                type="url" 
                id="meeting_link" 
                placeholder="https://meet.google.com/..." 
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="notes">Notes for Interviewer (Optional)</Label>
              <textarea 
                id="notes" 
                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50" 
                placeholder="Focus on React and system design..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </CardContent>

          <CardFooter className="flex justify-end gap-3 border-t bg-gray-50/50 px-6 py-4">
            <Link href="/dashboard/interviews" className={buttonVariants({ variant: "outline" })}>
              Cancel
            </Link>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700" disabled={isSubmitting || loading}>
              {(isSubmitting || loading) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Schedule Interview
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
