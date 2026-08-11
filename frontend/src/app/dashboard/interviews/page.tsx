"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Calendar, Clock, User, Video, Plus, MessageSquarePlus, Loader2, RefreshCw } from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface InterviewFeedback {
  id: string;
  interview_id: string;
  raw_notes: string;
  ai_summary: string;
  ai_strengths: string[];
  ai_weaknesses: string[];
  ai_recommendation: "Strong Hire" | "Hire" | "No Hire" | "Strong No Hire";
  overall_score: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Score Gauge (pure CSS — no Recharts import needed for a radial badge)
// ---------------------------------------------------------------------------

function ScoreGauge({ score }: { score: number }) {
  const pct = Math.round((score / 10) * 100);
  const color =
    score >= 8 ? "#10b981" : score >= 6 ? "#6366f1" : score >= 4 ? "#f59e0b" : "#ef4444";

  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="8" />
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 48 48)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text x="48" y="53" textAnchor="middle" fontSize="18" fontWeight="bold" fill={color}>
          {score.toFixed(1)}
        </text>
      </svg>
      <span className="text-xs text-gray-500 font-medium">out of 10</span>
    </div>
  );
}

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
// Feedback Results Panel
// ---------------------------------------------------------------------------

function FeedbackPanel({ feedback }: { feedback: InterviewFeedback }) {
  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      {/* Score + Recommendation row */}
      <div className="flex items-center gap-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
        <ScoreGauge score={feedback.overall_score} />
        <div className="space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Recommendation</p>
          <RecommendationBadge value={feedback.ai_recommendation} />
        </div>
      </div>

      {/* Summary */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-1.5">Summary</h4>
        <p className="text-sm text-gray-600 leading-relaxed">{feedback.ai_summary}</p>
      </div>

      {/* Strengths */}
      {feedback.ai_strengths?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Strengths</h4>
          <div className="flex flex-wrap gap-2">
            {feedback.ai_strengths.map((s, i) => (
              <span
                key={i}
                className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-medium"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Weaknesses */}
      {feedback.ai_weaknesses?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Areas for Concern</h4>
          <div className="flex flex-wrap gap-2">
            {feedback.ai_weaknesses.map((w, i) => (
              <span
                key={i}
                className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs font-medium"
              >
                {w}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Feedback Modal
// ---------------------------------------------------------------------------

function FeedbackModal({
  interviewId,
  open,
  onClose,
  existingFeedback,
  onSaved,
}: {
  interviewId: string;
  open: boolean;
  onClose: () => void;
  existingFeedback: InterviewFeedback | null;
  onSaved: (fb: InterviewFeedback) => void;
}) {
  const [notes, setNotes] = useState(existingFeedback?.raw_notes ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<InterviewFeedback | null>(existingFeedback);
  const [editing, setEditing] = useState(!existingFeedback);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setNotes(existingFeedback?.raw_notes ?? "");
      setResult(existingFeedback);
      setEditing(!existingFeedback);
      setError(null);
    }
  }, [open, existingFeedback]);

  const handleSubmit = async () => {
    if (!notes.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(
        `${API_BASE}/api/v1/interviews/${interviewId}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ raw_notes: notes }),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message ?? `Error ${res.status}`);
      }
      const fb: InterviewFeedback = await res.json();
      setResult(fb);
      setEditing(false);
      onSaved(fb);
    } catch (err: any) {
      setError(err.message ?? "Failed to generate feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold text-gray-900">
            Interview Feedback
          </DialogTitle>
          <DialogDescription className="text-sm text-gray-500">
            {editing
              ? "Enter your interview notes — AI will generate a structured evaluation."
              : "AI-generated evaluation based on your notes."}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-2 space-y-4">
          {/* Notes input (visible in edit mode) */}
          {editing && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Your Raw Notes
              </label>
              <Textarea
                id="feedback-notes"
                placeholder="Describe how the interview went — candidate's answers, communication style, technical depth, red flags, standout moments…"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={8}
                className="resize-none text-sm"
                disabled={submitting}
              />
              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                  {error}
                </p>
              )}
              <div className="flex justify-end gap-2 pt-1">
                <Button variant="ghost" onClick={onClose} disabled={submitting}>
                  Cancel
                </Button>
                <Button
                  id="submit-feedback-btn"
                  onClick={handleSubmit}
                  disabled={submitting || !notes.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white min-w-[140px]"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Analysing…
                    </>
                  ) : (
                    "Generate Feedback"
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Results panel */}
          {!editing && result && (
            <>
              <FeedbackPanel feedback={result} />
              <div className="flex justify-between items-center pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  Last generated {format(new Date(result.created_at), "MMM d, yyyy · h:mm a")}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditing(true)}
                  className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                  Edit Notes / Regenerate
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function InterviewsPage() {
  const { user, checkRole } = useAuth();
  const [interviews, setInterviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Feedback modal state
  const [feedbackModal, setFeedbackModal] = useState<{
    open: boolean;
    interviewId: string;
    existingFeedback: InterviewFeedback | null;
  }>({ open: false, interviewId: "", existingFeedback: null });

  // Track which interviews already have feedback (loaded lazily)
  const [feedbackMap, setFeedbackMap] = useState<Record<string, InterviewFeedback>>({});

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  useEffect(() => {
    const fetchInterviews = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${API_BASE}/api/v1/interviews`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setInterviews(data);
          const initialMap: Record<string, InterviewFeedback> = {};
          data.forEach((i: any) => {
            if (i.feedback) {
              initialMap[i.id] = i.feedback;
            }
          });
          setFeedbackMap((prev) => ({ ...initialMap, ...prev }));
        }
      } catch {
        console.error("Failed to fetch interviews");
      } finally {
        setLoading(false);
      }
    };
    fetchInterviews();
  }, [token]);

  const loadFeedback = useCallback(
    async (interviewId: string): Promise<InterviewFeedback | null> => {
      // Return cached if already loaded
      if (feedbackMap[interviewId]) return feedbackMap[interviewId];
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(
          `${API_BASE}/api/v1/interviews/${interviewId}/feedback`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          const fb: InterviewFeedback = await res.json();
          setFeedbackMap((prev) => ({ ...prev, [interviewId]: fb }));
          return fb;
        }
      } catch {}
      return null;
    },
    [feedbackMap, token]
  );

  const openFeedbackModal = async (interviewId: string) => {
    const existing = await loadFeedback(interviewId);
    setFeedbackModal({ open: true, interviewId, existingFeedback: existing });
  };

  const handleFeedbackSaved = (fb: InterviewFeedback) => {
    setFeedbackMap((prev) => ({ ...prev, [fb.interview_id]: fb }));
    setFeedbackModal((prev) => ({ ...prev, existingFeedback: fb }));
  };

  const canSchedule = checkRole(["hr_manager", "recruiter"]);
  const canSubmitFeedback = checkRole(["hr_manager", "recruiter", "interviewer"]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Interviews</h1>
          <p className="text-gray-500 mt-1">Manage and track candidate interviews.</p>
        </div>
        {canSchedule && (
          <Link 
            href="/dashboard/interviews/new" 
            className="inline-flex items-center justify-center rounded-md font-medium h-9 px-4 text-sm bg-indigo-600 text-white hover:bg-indigo-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Schedule Interview
          </Link>
        )}
      </div>

      <div className="grid gap-4">
        {interviews.map((interview) => {
          const hasFeedback = !!feedbackMap[interview.id];
          return (
            <Card key={interview.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">

                  {/* Left side: Candidate & Job */}
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg shrink-0">
                      {interview.candidate_name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-lg">
                        <Link
                          href={`/dashboard/interviews/${interview.id}`}
                          className="hover:text-indigo-600 transition-colors"
                        >
                          {interview.candidate_name}
                        </Link>
                      </h3>
                      <p className="text-gray-500 text-sm">{interview.job_title}</p>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <User className="h-4 w-4 text-gray-400" />
                          {interview.interviewer_name}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right side: Time & Actions */}
                  <div className="flex flex-col md:items-end gap-2">
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                      <Calendar className="h-4 w-4 text-indigo-500" />
                      {format(new Date(interview.scheduled_at), "MMM d, yyyy")}
                      <span className="text-gray-300">|</span>
                      <Clock className="h-4 w-4 text-indigo-500" />
                      {format(new Date(interview.scheduled_at), "h:mm a")} ({interview.duration_minutes}m)
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                      <span
                        className={`px-2.5 py-1 text-xs font-semibold rounded-full border capitalize
                          ${interview.status === "completed"
                            ? "bg-green-50 text-green-700 border-green-200"
                            : "bg-blue-50 text-blue-700 border-blue-200"
                          }`}
                      >
                        {interview.status}
                      </span>

                      {interview.status === "scheduled" && (
                        <Button variant="outline" size="sm" className="h-7 text-xs flex items-center gap-1">
                          <Video className="h-3 w-3" /> Join Call
                        </Button>
                      )}

                      {/* Feedback button — visible to all feedback-eligible roles */}
                      {canSubmitFeedback && (
                        <Button
                          id={`feedback-btn-${interview.id}`}
                          variant={hasFeedback ? "outline" : "default"}
                          size="sm"
                          className={`h-7 text-xs flex items-center gap-1 ${
                            hasFeedback
                              ? "border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                              : "bg-indigo-600 hover:bg-indigo-700 text-white"
                          }`}
                          onClick={() => openFeedbackModal(interview.id)}
                        >
                          <MessageSquarePlus className="h-3.5 w-3.5" />
                          {hasFeedback ? "View Feedback" : "Add Feedback"}
                        </Button>
                      )}

                      <Link 
                        href={`/dashboard/interviews/${interview.id}`}
                        className="inline-flex items-center justify-center rounded-md font-medium h-7 px-2 text-xs text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                      >
                        {interview.status === "completed" ? "View Notes" : "Details"}
                      </Link>
                    </div>
                  </div>

                </div>
              </CardContent>
            </Card>
          );
        })}

        {interviews.length === 0 && !loading && (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900">No interviews found</h3>
            <p className="text-gray-500 mt-1">There are no interviews scheduled at this time.</p>
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {feedbackModal.open && (
        <FeedbackModal
          interviewId={feedbackModal.interviewId}
          open={feedbackModal.open}
          onClose={() => setFeedbackModal((prev) => ({ ...prev, open: false }))}
          existingFeedback={feedbackModal.existingFeedback}
          onSaved={handleFeedbackSaved}
        />
      )}
    </div>
  );
}
