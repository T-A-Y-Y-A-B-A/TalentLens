"use client";

import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Clock, User, Video, Plus } from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";

// Mock data
const MOCK_INTERVIEWS = [
  {
    id: "1",
    candidate_name: "Alice Johnson",
    job_title: "Senior Frontend Engineer",
    scheduled_at: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
    duration_minutes: 60,
    status: "scheduled",
    interviewer: "Jane Smith",
  },
  {
    id: "2",
    candidate_name: "Bob Williams",
    job_title: "Product Manager",
    scheduled_at: new Date(Date.now() + 172800000).toISOString(), // In 2 days
    duration_minutes: 45,
    status: "scheduled",
    interviewer: "Mark Davis",
  },
  {
    id: "3",
    candidate_name: "Charlie Brown",
    job_title: "DevOps Engineer",
    scheduled_at: new Date(Date.now() - 86400000).toISOString(), // Yesterday
    duration_minutes: 60,
    status: "completed",
    interviewer: "Jane Smith",
  }
];

export default function InterviewsPage() {
  const { user, checkRole } = useAuth();
  const [interviews] = useState(MOCK_INTERVIEWS);

  const canSchedule = checkRole(["hr_manager", "recruiter"]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Interviews</h1>
          <p className="text-gray-500 mt-1">Manage and track candidate interviews.</p>
        </div>
        {canSchedule && (
          <Button asChild className="bg-indigo-600 hover:bg-indigo-700">
            <Link href="/dashboard/interviews/new">
              <Plus className="mr-2 h-4 w-4" />
              Schedule Interview
            </Link>
          </Button>
        )}
      </div>

      <div className="grid gap-4">
        {interviews.map((interview) => (
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
                      <Link href={`/dashboard/interviews/${interview.id}`} className="hover:text-indigo-600 transition-colors">
                        {interview.candidate_name}
                      </Link>
                    </h3>
                    <p className="text-gray-500 text-sm">{interview.job_title}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <User className="h-4 w-4 text-gray-400" />
                        {interview.interviewer}
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
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border capitalize
                      ${interview.status === 'completed' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-blue-50 text-blue-700 border-blue-200'}
                    `}>
                      {interview.status}
                    </span>
                    {interview.status === 'scheduled' && (
                      <Button variant="outline" size="sm" className="h-7 text-xs flex items-center gap-1">
                        <Video className="h-3 w-3" /> Join Call
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="h-7 text-xs text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50" asChild>
                      <Link href={`/dashboard/interviews/${interview.id}`}>
                        {interview.status === 'completed' ? 'View Notes' : 'Details'}
                      </Link>
                    </Button>
                  </div>
                </div>

              </div>
            </CardContent>
          </Card>
        ))}

        {interviews.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900">No interviews found</h3>
            <p className="text-gray-500 mt-1">There are no interviews scheduled at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
