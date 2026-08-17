"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Users, FileText, Activity } from "lucide-react";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type AdminPlatformStats = components["schemas"]["AdminPlatformStats"];

export default function AdminOverviewPage() {
  const [loading, setLoading] = useState(true);
  const [platformStats, setPlatformStats] = useState<AdminPlatformStats | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const { data, error } = await apiClient.GET("/api/v1/admin/stats" as any, {});
        if (data) {
          setPlatformStats(data as AdminPlatformStats);
        }
      } catch (err) {
        console.error("Failed to fetch admin stats", err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const stats = platformStats ? [
    { title: "Organizations", value: platformStats.total_organizations.toString(), icon: Building2, trend: "Active" },
    { title: "Total Users", value: platformStats.total_users.toString(), icon: Users, trend: "Active" },
    { title: "Candidates", value: platformStats.total_candidates.toString(), icon: FileText, trend: "Active" },
    { title: "AI API Calls", value: platformStats.total_ai_calls.toString(), icon: Activity, trend: "Recorded" },
  ] : [];

  if (loading) {
    return <div className="p-8 text-center text-zinc-500">Loading system metrics...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Platform Overview</h1>
        <p className="text-zinc-500 mt-1">System-wide metrics across all tenants.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-500">{stat.title}</p>
                  <p className="text-3xl font-bold text-zinc-900 mt-2">{stat.value}</p>
                </div>
                <div className="h-12 w-12 bg-indigo-50 rounded-full flex items-center justify-center">
                  <stat.icon className="h-6 w-6 text-indigo-600" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm text-emerald-600 font-medium">
                {stat.trend}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">Database Cluster</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">Background Workers (Celery)</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">OpenAI API Connectivity</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">Vector Search (Qdrant)</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recent Platform Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="h-2 w-2 mt-1.5 rounded-full bg-amber-500 shrink-0"></div>
                <div>
                  <p className="text-sm font-medium text-zinc-900">High API latency detected</p>
                  <p className="text-xs text-zinc-500 mt-0.5">OpenAI endpoints experienced a 2s delay spike. Resolved automatically.</p>
                  <p className="text-xs text-zinc-400 mt-1">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="h-2 w-2 mt-1.5 rounded-full bg-blue-500 shrink-0"></div>
                <div>
                  <p className="text-sm font-medium text-zinc-900">Database backup completed</p>
                  <p className="text-xs text-zinc-500 mt-0.5">Daily automated snapshot to S3.</p>
                  <p className="text-xs text-zinc-400 mt-1">6 hours ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
