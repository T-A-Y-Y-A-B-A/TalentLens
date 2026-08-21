"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Briefcase,
  Users,
  UserPlus,
  Clock,
  Sparkles,
  TrendingUp,
  ArrowRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

interface DashboardStats {
  active_jobs: number;
  total_candidates: number;
  interviews_today: number;
  new_applications_24h: number;
}

export default function DashboardOverviewPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || !user) return;
    const fetchStats = async () => {
      setStatsLoading(true);
      setStatsError(null);
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/v1/dashboard/stats", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err?.detail || `HTTP ${res.status}`);
        }
        setStats(await res.json());
      } catch (e: any) {
        setStatsError(e.message || "Failed to load stats");
      } finally {
        setStatsLoading(false);
      }
    };
    fetchStats();
  }, [user, authLoading]);

  const displayName =
    user?.email
      ? user.email
          .split("@")[0]
          .replace(/[._]/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase())
      : "there";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">
            Welcome back, {displayName}
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Here&apos;s what&apos;s happening in your organization today.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="inline-block h-2 w-2 rounded-full bg-[var(--pass)] animate-pulse" />
          Live data · {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
        </div>
      </div>

      {/* Stats Error Banner */}
      {statsError && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>Could not load stats: {statsError}</span>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Active Jobs"
          value={stats?.active_jobs}
          loading={statsLoading}
          icon={<Briefcase className="h-5 w-5 text-primary" />}
          iconBg="bg-accent"
          border="border-border"
          description="Currently open positions"
          href="/dashboard/jobs"
        />
        <StatCard
          label="Total Candidates"
          value={stats?.total_candidates}
          loading={statsLoading}
          icon={<Users className="h-5 w-5 text-primary" />}
          iconBg="bg-accent"
          border="border-border"
          description="Applied to your org"
          href="/dashboard/candidates"
        />
        <StatCard
          label="Interviews Today"
          value={stats?.interviews_today}
          loading={statsLoading}
          icon={<Clock className="h-5 w-5 text-primary" />}
          iconBg="bg-accent"
          border="border-border"
          description="Scheduled for today (UTC)"
          href="/dashboard/interviews"
        />
        <StatCard
          label="New Applications"
          value={stats?.new_applications_24h}
          loading={statsLoading}
          icon={<TrendingUp className="h-5 w-5 text-primary" />}
          iconBg="bg-accent"
          border="border-border"
          description="In the last 24 hours"
          href="/dashboard/candidates"
        />
      </div>

      {/* Quick Actions */}
      {user?.role !== "interviewer" && (
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <QuickActionCard
              href="/dashboard/jobs/new"
              icon={<Briefcase className="h-6 w-6 text-primary" />}
              iconBg="bg-accent"
              title="Create New Job"
              description="Post a new open position with a custom pipeline"
            />
            {user?.role === "hr_manager" && (
              <QuickActionCard
                href="/dashboard/invite-member"
                icon={<UserPlus className="h-6 w-6 text-primary" />}
                iconBg="bg-accent"
                title="Invite Team Member"
                description="Send a signed invite link to a recruiter or interviewer"
              />
            )}
            <QuickActionCard
              href="/dashboard/copilot"
              icon={<Sparkles className="h-6 w-6 text-primary" />}
              iconBg="bg-accent"
              title="AI Candidate Search"
              description="Semantic search across your candidate pool with AI"
            />
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Sub-components ───────────────────────────────────────────────────────── */

function StatCard({
  label,
  value,
  loading,
  icon,
  iconBg,
  border,
  description,
  href,
}: {
  label: string;
  value?: number;
  loading: boolean;
  icon: React.ReactNode;
  iconBg: string;
  border: string;
  description: string;
  href: string;
}) {
  return (
    <Link href={href} className="group block">
      <Card
        className={`border ${border} shadow-sm transition-all duration-200 group-hover:shadow-md group-hover:-translate-y-0.5`}
      >
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {label}
              </p>
              <div className="mt-2">
                {loading ? (
                  <div className="h-8 w-16 rounded bg-secondary animate-pulse" />
                ) : (
                  <p className="text-3xl font-bold font-mono text-foreground tabular-nums">
                    {value?.toLocaleString() ?? "—"}
                  </p>
                )}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            </div>
            <div
              className={`ml-3 h-10 w-10 flex-shrink-0 ${iconBg} rounded-xl flex items-center justify-center`}
            >
              {icon}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function QuickActionCard({
  href,
  icon,
  iconBg,
  title,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  description: string;
}) {
  return (
    <Link href={href} className="group block h-full">
      <Card className="border border-border shadow-sm transition-all duration-200 group-hover:shadow-md group-hover:-translate-y-0.5 group-hover:border-primary/50 h-full">
        <CardContent className="p-5 flex items-start gap-4 h-full">
          <div
            className={`${iconBg} h-11 w-11 flex-shrink-0 rounded-xl flex items-center justify-center transition-transform duration-200 group-hover:scale-110`}
          >
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground text-sm leading-tight group-hover:text-primary transition-colors duration-150">
              {title}
            </p>
            <p className="mt-1 text-xs text-muted-foreground leading-snug">
              {description}
            </p>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all duration-150 self-center flex-shrink-0" />
        </CardContent>
      </Card>
    </Link>
  );
}
