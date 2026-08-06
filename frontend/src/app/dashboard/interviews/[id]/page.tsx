"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ArrowLeft, CheckCircle2, Loader2, Video, Calendar, Clock, User, Briefcase } from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";

export default function InterviewDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Mock save delay
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
      setTimeout(() => {
        router.push("/dashboard/interviews");
      }, 2000);
    }, 1000);
  };

  // Mock data for the view
  const interview = {
    id: params.id,
    candidate_name: "Alice Johnson",
    job_title: "Senior Frontend Engineer",
    scheduled_at: new Date(Date.now() + 86400000).toISOString(),
    duration_minutes: 60,
    status: "scheduled",
    interviewer: "Jane Smith",
    notes: "Focus on React performance and state management architecture."
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild className="rounded-full">
          <Link href="/dashboard/interviews">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Interview Details</h1>
          <p className="text-gray-500 mt-1">View details and submit your evaluation.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="md:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <User className="h-5 w-5 text-indigo-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Candidate</p>
                  <p className="text-sm text-gray-500">{interview.candidate_name}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Briefcase className="h-5 w-5 text-indigo-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Position</p>
                  <p className="text-sm text-gray-500">{interview.job_title}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-indigo-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Date & Time</p>
                  <p className="text-sm text-gray-500">{format(new Date(interview.scheduled_at), "PPP")}</p>
                  <p className="text-sm text-gray-500">{format(new Date(interview.scheduled_at), "p")} ({interview.duration_minutes}m)</p>
                </div>
              </div>
              
              <div className="pt-4 border-t">
                <Button className="w-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200">
                  <Video className="mr-2 h-4 w-4" /> Join Video Call
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Pre-Interview Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md italic">
                "{interview.notes}"
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Feedback Form */}
        <div className="md:col-span-2">
          <Card>
            <form onSubmit={handleSubmit}>
              <CardHeader>
                <CardTitle>Submit Feedback</CardTitle>
                <CardDescription>Evaluate the candidate's performance during the interview.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {isSubmitted && (
                  <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-md flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5" />
                    <p className="text-sm font-medium">Feedback submitted successfully! Redirecting...</p>
                  </div>
                )}

                <div className="grid gap-3">
                  <Label>Overall Recommendation</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="recommendation" value="strong_yes" required className="text-indigo-600 focus:ring-indigo-600" />
                      <span className="text-sm font-medium text-green-700 bg-green-50 px-2 py-1 rounded-md">Strong Yes</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="recommendation" value="yes" required className="text-indigo-600 focus:ring-indigo-600" />
                      <span className="text-sm font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded-md">Yes</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="recommendation" value="no" required className="text-indigo-600 focus:ring-indigo-600" />
                      <span className="text-sm font-medium text-red-700 bg-red-50 px-2 py-1 rounded-md">No</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="recommendation" value="strong_no" required className="text-indigo-600 focus:ring-indigo-600" />
                      <span className="text-sm font-medium text-red-900 bg-red-100 px-2 py-1 rounded-md">Strong No</span>
                    </label>
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="technical">Technical Skills Assessment</Label>
                  <textarea 
                    id="technical" 
                    required
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" 
                    placeholder="Evaluate their technical answers..."
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="communication">Communication & Culture Fit</Label>
                  <textarea 
                    id="communication" 
                    required
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" 
                    placeholder="Evaluate their communication skills..."
                  />
                </div>
              </CardContent>

              <CardFooter className="flex justify-end gap-3 border-t bg-gray-50/50 px-6 py-4">
                <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700" disabled={isSubmitting || isSubmitted}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Submit Feedback
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
