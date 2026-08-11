"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Users, Timer, TrendingUp, Sparkles, Building, Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const PIE_COLORS = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b"];

interface TrendDataPoint { month: string; applied: number; hired: number; }
interface DeptDataPoint { name: string; hires: number; }
interface SourceDataPoint { name: string; value: number; }
interface AnalyticsData {
  time_to_hire_days: number;
  time_to_hire_trend: number;
  pipeline_conversion_pct: number;
  pipeline_conversion_trend: number;
  ai_match_success_pct: number;
  active_jobs_count: number;
  active_jobs_depts: number;
  pipeline_trend_data: TrendDataPoint[];
  dept_data: DeptDataPoint[];
  source_data: SourceDataPoint[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const token = localStorage.getItem("access_token") || "";
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${API_BASE}/api/v1/analytics/dashboard`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to load analytics");
        
        const jsonData = await res.json();
        setData(jsonData);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center text-red-500">
        Error loading analytics: {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">Overview of your organization's hiring performance.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Time to Hire</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{data.time_to_hire_days} days</h3>
              </div>
              <div className="h-12 w-12 bg-blue-50 rounded-full flex items-center justify-center">
                <Timer className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="h-4 w-4 mr-1" />
              <span>{data.time_to_hire_trend}% faster</span>
              <span className="text-gray-400 ml-2">vs last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Pipeline Conversion</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{data.pipeline_conversion_pct}%</h3>
              </div>
              <div className="h-12 w-12 bg-indigo-50 rounded-full flex items-center justify-center">
                <Users className="h-6 w-6 text-indigo-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="h-4 w-4 mr-1" />
              <span>{data.pipeline_conversion_trend}% increase</span>
              <span className="text-gray-400 ml-2">vs last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">AI Match Success</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{data.ai_match_success_pct}%</h3>
              </div>
              <div className="h-12 w-12 bg-purple-50 rounded-full flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Top 10 AI matches reaching interview stage
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Active Jobs</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{data.active_jobs_count}</h3>
              </div>
              <div className="h-12 w-12 bg-amber-50 rounded-full flex items-center justify-center">
                <Building className="h-6 w-6 text-amber-600" />
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Across {data.active_jobs_depts} departments
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Candidates vs Hires</CardTitle>
            <CardDescription>Pipeline volume over the last 6 months</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.pipeline_trend_data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} />
                  <YAxis axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="applied" stroke="#4f46e5" strokeWidth={2} dot={false} name="Applied" />
                  <Line type="monotone" dataKey="hired" stroke="#10b981" strokeWidth={2} dot={false} name="Hired" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Hires by Department</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[180px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.dept_data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                    <XAxis type="number" axisLine={false} tickLine={false} />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} />
                    <Tooltip cursor={{fill: 'transparent'}} />
                    <Bar dataKey="hires" fill="#06b6d4" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sourcing Channels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[180px] w-full flex items-center">
                <div className="w-1/2 h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.source_data}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={70}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {data.source_data.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="w-1/2 flex flex-col justify-center space-y-2">
                  {data.source_data.map((entry, index) => (
                    <div key={entry.name} className="flex items-center text-sm">
                      <div 
                        className="w-3 h-3 rounded-full mr-2" 
                        style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} 
                      />
                      <span className="text-gray-600 flex-1">{entry.name}</span>
                      <span className="font-medium text-gray-900">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
