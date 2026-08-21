"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  ArrowLeft,
  Calendar,
  Clock,
  User,
  Briefcase,
  Video,
  Edit,
  Trash2,
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Mail,
  Phone,
  MessageSquarePlus,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  Globe
} from "lucide-react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { MatchGateBar } from "@/components/ui/match-gate-bar";

// ---------------------------------------------------------------------------
// Score Gauge removed (replaced by MatchGateBar)
// ---------------------------------------------------------------------------



// ---------------------------------------------------------------------------
// Recommendation Badge
// ---------------------------------------------------------------------------

const REC_STYLES: Record<string, string> = {
  "Strong Hire": "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Hire": "bg-green-100 text-green-700 border-green-300",
  "No Hire": "bg-orange-100 text-orange-700 border-orange-300",
  "Strong No Hire": "bg-red-100 text-red-700 border-red-300",
};

function RecommendationBadge({ value }: { value: string }) {
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full border text-sm font-semibold ${
        REC_STYLES[value] ?? "bg-gray-100 text-gray-700 border-gray-300"
      }`}
    >
      {value}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Status Badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const normalized = status?.toLowerCase() || "scheduled";
  switch (normalized) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 capitalize">
          <CheckCircle2 className="h-3.5 w-3.5" /> Completed
        </span>
      );
    case "cancelled":
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-red-50 text-red-700 border border-red-200 capitalize">
          <XCircle className="h-3.5 w-3.5" /> Cancelled
        </span>
      );
    case "no_show":
    case "no-show":
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200 capitalize">
          <AlertTriangle className="h-3.5 w-3.5" /> No-Show
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-200 capitalize">
          <Clock className="h-3.5 w-3.5" /> Scheduled
        </span>
      );
  }
}

// ---------------------------------------------------------------------------
// Interview Detail Page
// ---------------------------------------------------------------------------

export default function InterviewDetailPage() {
  const router = useRouter();
  const params = useParams();
  const interviewId = params.id as string;
  const { checkRole } = useAuth();

  const [interview, setInterview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // Feedback modal
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  // Edit / Reschedule state
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  const [editDate, setEditDate] = useState("");
  const [editTime, setEditTime] = useState("");
  const [editDuration, setEditDuration] = useState("60");
  const [editMeetingLink, setEditMeetingLink] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // Cancel / Status modal state
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);

  const canManage = checkRole(["hr_manager", "recruiter"]);

  const fetchInterview = useCallback(async () => {
    if (!interviewId) return;
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/v1/interviews/${interviewId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setInterview(data);
        setNotFound(false);

        if (data.scheduled_at) {
          const dt = data.scheduled_at.split("T");
          setEditDate(dt[0]);
          if (dt[1]) {
            setEditTime(dt[1].substring(0, 5));
          }
        }
        setEditDuration(data.duration_minutes?.toString() || "60");
        setEditMeetingLink(data.meeting_link || "");
        setEditNotes(data.notes || "");
      } else {
        setNotFound(true);
      }
    } catch (err) {
      console.error("Failed to fetch interview details");
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  useEffect(() => {
    fetchInterview();
  }, [fetchInterview]);

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmittingEdit) return;
    setIsSubmittingEdit(true);
    try {
      const scheduled_at = `${editDate}T${editTime}:00Z`;
      const token = localStorage.getItem("access_token");

      const payload = {
        scheduled_at,
        duration_minutes: parseInt(editDuration),
        meeting_link: editMeetingLink || null,
        notes: editNotes || null
      };

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/v1/interviews/${interviewId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        await fetchInterview();
        setIsEditing(false);
      }
    } catch (err) {
      console.error("Interview edit request failed");
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const updateStatus = async (newStatus: string) => {
    setStatusUpdating(true);
    try {
      const token = localStorage.getItem("access_token");
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/v1/interviews/${interviewId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        await fetchInterview();
      }
    } catch (err) {
      console.error("Failed to update status");
    } finally {
      setStatusUpdating(false);
      setShowCancelConfirm(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackNotes.trim()) return;
    setSubmittingFeedback(true);
    setFeedbackError(null);
    try {
      const token = localStorage.getItem("access_token");
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/v1/interviews/${interviewId}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ raw_notes: feedbackNotes }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message ?? `Error ${res.status}`);
      }
      setShowFeedbackModal(false);
      await fetchInterview();
    } catch (err: any) {
      setFeedbackError(err.message || "Failed to generate feedback");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (notFound || !interview) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 text-center bg-white rounded-xl border border-gray-200 shadow-sm space-y-4">
        <ShieldAlert className="h-12 w-12 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-gray-900">Interview Not Found</h2>
        <p className="text-sm text-gray-500">
          The requested interview could not be found or you do not have permission to view it within your organization.
        </p>
        <Link href="/dashboard/interviews" className={buttonVariants({ className: "bg-indigo-600 hover:bg-indigo-700 text-white" })}>
          Return to Interviews
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back button & Page Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard/interviews" className={buttonVariants({ variant: "ghost", size: "icon", className: "rounded-full shrink-0" })}>
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">
                Interview with {interview.candidate_name}
              </h1>
              <StatusBadge status={interview.status} />
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              Position: <span className="font-medium text-gray-700">{interview.job_title}</span>
            </p>
          </div>
        </div>

        {/* RBAC-Gated Quick Actions Header */}
        {canManage && (
          <div className="flex items-center gap-2 shrink-0">
            {interview.status === "scheduled" && (
              <>
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit className="mr-1.5 h-4 w-4 text-gray-500" /> Reschedule
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-emerald-700 border-emerald-200 hover:bg-emerald-50"
                  onClick={() => updateStatus("completed")}
                  disabled={statusUpdating}
                >
                  <CheckCircle2 className="mr-1.5 h-4 w-4" /> Mark Completed
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowCancelConfirm(true)}
                  disabled={statusUpdating}
                >
                  <Trash2 className="mr-1.5 h-4 w-4" /> Cancel
                </Button>
              </>
            )}
            {interview.status !== "scheduled" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => updateStatus("scheduled")}
                disabled={statusUpdating}
              >
                Re-open / Reschedule
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Left Column (2 Cols wide on desktop) */}
        <div className="lg:col-span-2 space-y-6">

          {/* Section 1: Header / Schedule Details */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4">
              <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-600" />
                Schedule & Details
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs uppercase font-medium text-gray-400">Date & Time</span>
                  <p className="text-sm font-semibold text-gray-900 mt-1">
                    {format(parseISO(interview.scheduled_at), "PPP · p")}
                  </p>
                </div>
                <div>
                  <span className="text-xs uppercase font-medium text-gray-400">Duration</span>
                  <p className="text-sm font-semibold text-gray-900 mt-1">
                    {interview.duration_minutes} minutes
                  </p>
                </div>
                <div>
                  <span className="text-xs uppercase font-medium text-gray-400">Timezone</span>
                  <p className="text-sm font-medium text-gray-700 mt-1 flex items-center gap-1.5">
                    <Globe className="h-3.5 w-3.5 text-gray-400" /> UTC (Coordinated Universal Time)
                  </p>
                </div>
                <div>
                  <span className="text-xs uppercase font-medium text-gray-400">Status</span>
                  <div className="mt-1">
                    <StatusBadge status={interview.status} />
                  </div>
                </div>
              </div>

              {interview.notes && (
                <div className="pt-3 border-t">
                  <span className="text-xs uppercase font-medium text-gray-400">Interviewer Notes</span>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg mt-1 italic">
                    "{interview.notes}"
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section 2: Participants */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4">
              <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <User className="h-4 w-4 text-indigo-600" />
                Participants
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Candidate Info */}
              <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-2">
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">Candidate</span>
                <p className="text-base font-bold text-gray-900">
                  <Link href={`/dashboard/candidates/${interview.candidate_id}`} className="hover:text-indigo-600 transition-colors">
                    {interview.candidate_name}
                  </Link>
                </p>
                {interview.candidate_email && (
                  <p className="text-xs text-gray-600 flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-gray-400 shrink-0" /> {interview.candidate_email}
                  </p>
                )}
                {interview.candidate_phone && (
                  <p className="text-xs text-gray-600 flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5 text-gray-400 shrink-0" /> {interview.candidate_phone}
                  </p>
                )}
              </div>

              {/* Interviewer Info */}
              <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-2">
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">Assigned Interviewer</span>
                <p className="text-base font-bold text-gray-900">{interview.interviewer_name}</p>
                <p className="text-xs text-gray-500 capitalize">
                  Role: <span className="font-medium text-gray-700">{interview.interviewer_role?.replace("_", " ") || "Interviewer"}</span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Section 3: Logistics */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4">
              <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <Video className="h-4 w-4 text-indigo-600" />
                Logistics & Video Call
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-4">
              {interview.meeting_link ? (
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-blue-50/60 border border-blue-100">
                  <div>
                    <p className="text-sm font-semibold text-blue-900">Online Video Conference</p>
                    <p className="text-xs text-blue-700 truncate max-w-md mt-0.5">{interview.meeting_link}</p>
                  </div>
                  <a href={interview.meeting_link} target="_blank" rel="noopener noreferrer" className={buttonVariants({ className: "bg-blue-600 hover:bg-blue-700 text-white shrink-0" })}>
                    <Video className="mr-2 h-4 w-4" /> Join Video Call
                  </a>
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">No meeting link assigned yet.</p>
              )}

              <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-lg">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>Calendar Invite & Email Notifications Dispatched to Participants</span>
              </div>
            </CardContent>
          </Card>

          {/* Section 5: AI Interview Feedback Panel */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
                  <MessageSquarePlus className="h-4 w-4 text-indigo-600" />
                  AI Interview Evaluation & Feedback
                </CardTitle>
                <CardDescription className="text-xs text-gray-500 mt-0.5">
                  Structured evaluation generated from interviewer notes
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                onClick={() => {
                  setFeedbackNotes(interview.feedback?.raw_notes || "");
                  setShowFeedbackModal(true);
                }}
              >
                {interview.feedback ? (
                  <>
                    <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Edit / Regenerate
                  </>
                ) : (
                  <>
                    <MessageSquarePlus className="mr-1.5 h-3.5 w-3.5" /> Add Feedback
                  </>
                )}
              </Button>
            </CardHeader>

            <CardContent className="pt-6">
              {interview.feedback ? (
                <div className="space-y-6">
                  {/* Score & Recommendation */}
                  <div className="flex items-center gap-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="w-32 shrink-0">
                      <MatchGateBar overallScore={Math.round((interview.feedback.overall_score || 0) * 10)} gateThreshold={70} />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Recommendation</p>
                      <RecommendationBadge value={interview.feedback.ai_recommendation || "Hire"} />
                    </div>
                  </div>

                  {/* Summary */}
                  <div>
                    <h4 className="text-xs uppercase tracking-wide font-bold text-gray-500 mb-1.5">Evaluation Summary</h4>
                    <p className="text-sm text-gray-700 leading-relaxed bg-gray-50/60 p-3.5 rounded-lg border border-gray-100">
                      {interview.feedback.ai_summary}
                    </p>
                  </div>

                  {/* Strengths */}
                  {interview.feedback.ai_strengths?.length > 0 && (
                    <div>
                      <h4 className="text-xs uppercase tracking-wide font-bold text-gray-500 mb-2">Key Strengths</h4>
                      <div className="flex flex-wrap gap-2">
                        {interview.feedback.ai_strengths.map((s: string, idx: number) => (
                          <span key={idx} className="px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-medium">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Weaknesses */}
                  {interview.feedback.ai_weaknesses?.length > 0 && (
                    <div>
                      <h4 className="text-xs uppercase tracking-wide font-bold text-gray-500 mb-2">Areas for Concern</h4>
                      <div className="flex flex-wrap gap-2">
                        {interview.feedback.ai_weaknesses.map((w: string, idx: number) => (
                          <span key={idx} className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs font-medium">
                            {w}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Raw Notes */}
                  {interview.feedback.raw_notes && (
                    <div className="pt-3 border-t">
                      <h4 className="text-xs uppercase tracking-wide font-bold text-gray-500 mb-1.5">Interviewer Raw Notes</h4>
                      <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg italic">
                        "{interview.feedback.raw_notes}"
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 space-y-3">
                  <MessageSquarePlus className="h-10 w-10 text-gray-300 mx-auto" />
                  <p className="text-sm text-gray-500">No evaluation notes have been submitted for this interview yet.</p>
                  <Button
                    className="bg-indigo-600 hover:bg-indigo-700 text-white"
                    onClick={() => {
                      setFeedbackNotes("");
                      setShowFeedbackModal(true);
                    }}
                  >
                    Submit Interview Notes & Generate Evaluation
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

        </div>

        {/* Sidebar (1 Col wide on desktop) */}
        <div className="space-y-6">

          {/* Section 6: Sidebar Links */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4">
              <CardTitle className="text-base font-semibold text-gray-900">Quick Navigation</CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-3">
              <Link href={`/dashboard/candidates/${interview.candidate_id}`} className={buttonVariants({ variant: "outline", className: "w-full justify-start text-sm" })}>
                <User className="mr-2 h-4 w-4 text-indigo-600" />
                View Candidate Profile
                <ExternalLink className="ml-auto h-3.5 w-3.5 text-gray-400" />
              </Link>

              <Link href={`/dashboard/jobs/${interview.job_id}`} className={buttonVariants({ variant: "outline", className: "w-full justify-start text-sm" })}>
                <Briefcase className="mr-2 h-4 w-4 text-indigo-600" />
                View Job Posting
                <ExternalLink className="ml-auto h-3.5 w-3.5 text-gray-400" />
              </Link>
            </CardContent>
          </Card>

          {/* Section 7: Audit Trail */}
          <Card>
            <CardHeader className="border-b bg-gray-50/50 pb-4">
              <CardTitle className="text-base font-semibold text-gray-900">Audit Trail</CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-3 text-xs text-gray-600">
              <div>
                <span className="font-semibold text-gray-700">Scheduled At:</span>
                <p className="text-gray-500 mt-0.5">
                  {interview.created_at ? format(parseISO(interview.created_at), "PPP · p") : "Recorded in system"}
                </p>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Primary Interviewer:</span>
                <p className="text-gray-500 mt-0.5">{interview.interviewer_name}</p>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Interview ID:</span>
                <p className="font-mono text-gray-400 text-[10px] break-all mt-0.5">{interview.id}</p>
              </div>
            </CardContent>
          </Card>

        </div>
      </div>

      {/* Reschedule / Edit Dialog Modal */}
      {isEditing && (
        <Dialog open={isEditing} onOpenChange={(v) => !v && setIsEditing(false)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Reschedule / Edit Interview</DialogTitle>
              <DialogDescription>Update date, time, duration, or meeting notes.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleEditSubmit} className="space-y-4 pt-2">
              <div className="grid gap-2">
                <Label>Date</Label>
                <Input type="date" required value={editDate} onChange={(e) => setEditDate(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Time</Label>
                <Input type="time" required value={editTime} onChange={(e) => setEditTime(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Duration (Minutes)</Label>
                <Input type="number" required value={editDuration} onChange={(e) => setEditDuration(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Meeting Link</Label>
                <Input type="url" value={editMeetingLink} onChange={(e) => setEditMeetingLink(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Notes</Label>
                <Textarea value={editNotes} onChange={(e) => setEditNotes(e.target.value)} rows={3} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
                <Button type="submit" disabled={isSubmittingEdit} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                  {isSubmittingEdit && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Save Changes
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Feedback Dialog Modal */}
      {showFeedbackModal && (
        <Dialog open={showFeedbackModal} onOpenChange={(v) => !v && setShowFeedbackModal(false)}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Interview Evaluation & Notes</DialogTitle>
              <DialogDescription>
                Enter raw notes from the interview. AI will analyze the feedback and generate structured recommendations.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <Textarea
                placeholder="Describe candidate answers, technical depth, red flags, soft skills..."
                rows={6}
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                disabled={submittingFeedback}
              />
              {feedbackError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 border border-red-200 rounded-md">{feedbackError}</p>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowFeedbackModal(false)} disabled={submittingFeedback}>
                  Cancel
                </Button>
                <Button
                  onClick={handleFeedbackSubmit}
                  disabled={submittingFeedback || !feedbackNotes.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {submittingFeedback ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing with AI...
                    </>
                  ) : (
                    "Generate AI Feedback"
                  )}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Cancel Confirmation Modal */}
      {showCancelConfirm && (
        <Dialog open={showCancelConfirm} onOpenChange={(v) => !v && setShowCancelConfirm(false)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Cancel Interview</DialogTitle>
              <DialogDescription>
                Are you sure you want to cancel this interview? This will mark the status as cancelled.
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowCancelConfirm(false)}>Keep Scheduled</Button>
              <Button variant="destructive" onClick={() => updateStatus("cancelled")} disabled={statusUpdating}>
                {statusUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Confirm Cancel
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
