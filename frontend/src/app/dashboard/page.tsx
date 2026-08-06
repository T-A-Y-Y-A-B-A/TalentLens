"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Briefcase, Users, UserPlus, Clock } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardOverviewPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Welcome back, {user?.email.split("@")[0] || "User"}!
        </h1>
        <p className="text-gray-500 mt-1">Here's what's happening in your organization today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Quick Stats */}
        <Card className="col-span-1 md:col-span-3 lg:col-span-1 border-indigo-100 shadow-sm bg-indigo-50/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-indigo-900">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild className="w-full justify-start bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50">
              <Link href="/dashboard/jobs/new">
                <Briefcase className="mr-2 h-4 w-4" /> Create New Job
              </Link>
            </Button>
            <Button asChild className="w-full justify-start bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50">
              <Link href="/dashboard/settings/users">
                <UserPlus className="mr-2 h-4 w-4" /> Invite Team Member
              </Link>
            </Button>
            <Button asChild className="w-full justify-start bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50">
              <Link href="/dashboard/copilot">
                <Users className="mr-2 h-4 w-4" /> AI Candidate Search
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Overview Cards */}
        <div className="col-span-1 md:col-span-3 lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Active Jobs</p>
                  <h3 className="text-2xl font-bold text-gray-900 mt-1">14</h3>
                </div>
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Briefcase className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Candidates</p>
                  <h3 className="text-2xl font-bold text-gray-900 mt-1">1,248</h3>
                </div>
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <Users className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Interviews Today</p>
                  <h3 className="text-2xl font-bold text-gray-900 mt-1">6</h3>
                </div>
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <Clock className="h-5 w-5 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">New Applications</p>
                  <h3 className="text-2xl font-bold text-gray-900 mt-1">32</h3>
                </div>
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <UserPlus className="h-5 w-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
