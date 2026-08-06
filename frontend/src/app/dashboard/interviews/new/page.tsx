"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

export default function ScheduleInterviewPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Mock save delay
    setTimeout(() => {
      router.push("/dashboard/interviews");
    }, 1000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild className="rounded-full">
          <Link href="/dashboard/interviews">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Schedule Interview</h1>
          <p className="text-gray-500 mt-1">Set up a new interview with a candidate.</p>
        </div>
      </div>

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
              >
                <option value="" disabled selected>Select a candidate</option>
                <option value="c1">Alice Johnson - Senior Frontend Engineer</option>
                <option value="c2">Bob Williams - Product Manager</option>
                <option value="c3">Charlie Brown - DevOps Engineer</option>
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="interviewer">Interviewer</Label>
              <select
                id="interviewer"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
              >
                <option value="" disabled selected>Select an interviewer</option>
                <option value="u1">Jane Smith (HR Manager)</option>
                <option value="u2">Mark Davis (Interviewer)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="date">Date</Label>
                <Input type="date" id="date" required />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="time">Time</Label>
                <Input type="time" id="time" required />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="duration">Duration</Label>
              <select
                id="duration"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                defaultValue="60"
                required
              >
                <option value="30">30 minutes</option>
                <option value="45">45 minutes</option>
                <option value="60">60 minutes (1 hour)</option>
                <option value="90">90 minutes (1.5 hours)</option>
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="notes">Notes for Interviewer (Optional)</Label>
              <textarea 
                id="notes" 
                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50" 
                placeholder="Focus on React and system design..."
              />
            </div>
          </CardContent>

          <CardFooter className="flex justify-end gap-3 border-t bg-gray-50/50 px-6 py-4">
            <Button type="button" variant="outline" asChild>
              <Link href="/dashboard/interviews">Cancel</Link>
            </Button>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Schedule Interview
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
