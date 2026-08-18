"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, FileText, CheckCircle2, Clock, XCircle, ArrowRight, X } from "lucide-react";
import { format } from "date-fns";

type Application = {
  id: string;
  job_id: string;
  job_title?: string;
  stage_name?: string;
  status: string;
  applied_at: string;
};

export default function CandidateApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null);

  const fetchApplications = async () => {
    try {
      const { data, error } = await apiClient.GET("/api/v1/candidate-portal/applications", {});
      if (data) {
        setApplications(data as unknown as Application[]);
      }
    } catch (err) {
      console.error("Failed to fetch applications", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleWithdraw = async (appId: string) => {
    if (!confirm("Are you sure you want to withdraw this application? This cannot be undone.")) return;
    setWithdrawingId(appId);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/applications/${appId}/withdraw`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        await fetchApplications();
      } else {
        alert("Failed to withdraw application.");
      }
    } catch (err) {
      console.error(err);
      alert("Error withdrawing application.");
    } finally {
      setWithdrawingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  const getStatusBadge = (status: string, stageName?: string) => {
    // If the application is rejected or withdrawn
    if (status === "rejected") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-red-50 text-red-700 border border-red-100">
          <XCircle className="h-3.5 w-3.5" />
          Rejected
        </span>
      );
    }

    // Determine color based on stage name roughly
    const stage = (stageName || "").toLowerCase();
    
    if (stage.includes("offer") || stage.includes("hired")) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
          <CheckCircle2 className="h-3.5 w-3.5" />
          {stageName}
        </span>
      );
    }

    if (stage.includes("interview")) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
          <Clock className="h-3.5 w-3.5" />
          {stageName}
        </span>
      );
    }

    // Default active stage
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
        <ArrowRight className="h-3.5 w-3.5" />
        {stageName || "In Progress"}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">My Applications</h1>
        <p className="text-zinc-500 mt-2">Track the status of your active job applications.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Application History</CardTitle>
          <CardDescription>
            You have {applications.length} active application{applications.length !== 1 ? 's' : ''}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {applications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center border-2 border-dashed border-zinc-200 rounded-xl bg-zinc-50/50">
              <FileText className="h-12 w-12 text-zinc-300 mb-4" />
              <h3 className="text-lg font-medium text-zinc-900">No applications found</h3>
              <p className="text-zinc-500 mt-1 mb-4 text-sm max-w-sm">
                You haven't applied to any jobs yet. Head over to the job board to find your next opportunity.
              </p>
            </div>
          ) : (
            <div className="rounded-md border border-zinc-200">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50 hover:bg-zinc-50">
                    <TableHead className="w-[40%] text-zinc-900 font-semibold">Job Title</TableHead>
                    <TableHead className="text-zinc-900 font-semibold">Date Applied</TableHead>
                    <TableHead className="text-zinc-900 font-semibold">Current Status</TableHead>
                    <TableHead className="text-right text-zinc-900 font-semibold">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {applications.map((app) => (
                    <TableRow key={app.id}>
                      <TableCell className="font-medium text-zinc-900">
                        {app.job_title || "Unknown Job"}
                      </TableCell>
                      <TableCell className="text-zinc-500">
                        {format(new Date(app.applied_at), "MMM d, yyyy")}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(app.status, app.stage_name)}
                      </TableCell>
                      <TableCell className="text-right">
                        {!["rejected", "withdrawn", "hired"].includes(app.status.toLowerCase()) && (
                          <button
                            onClick={() => handleWithdraw(app.id)}
                            disabled={withdrawingId === app.id}
                            className="text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50"
                          >
                            {withdrawingId === app.id ? "Withdrawing..." : "Withdraw"}
                          </button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
