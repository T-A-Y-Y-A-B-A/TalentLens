"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { Loader2, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CandidatePortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-50">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-900" />
      </div>
    );
  }

  // Candidate portal expects a user, but specifically one WITHOUT hr roles.
  // We'll enforce that they are logged in.
  if (!user) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-zinc-50 p-4 text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-2">Not Authenticated</h1>
        <p className="text-zinc-600 mb-6">
          Please log in to access the candidate portal.
        </p>
        <Button onClick={() => window.location.href = "/candidate/login"} variant="outline">
          Go to Login
        </Button>
      </div>
    );
  }

  // For now, if they are an HR user trying to access the candidate portal, we just show a warning
  // In reality, candidate auth might be completely separate tokens.
  const isHR = ["hr_manager", "hr_admin", "recruiter"].includes(user.role);

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      {/* Simple Top Nav for Candidate */}
      <header className="bg-white border-b border-zinc-200 h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center">
          <span className="text-xl font-bold text-zinc-900 tracking-tight">TalentLens Portal</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-zinc-600 hidden sm:inline-block">
            {user.email}
          </span>
          <button
            onClick={logout}
            className="text-zinc-500 hover:text-zinc-700 flex items-center text-sm font-medium"
          >
            <LogOut className="h-4 w-4 mr-1" />
            <span className="hidden sm:inline-block">Sign out</span>
          </button>
        </div>
      </header>

      {isHR && (
        <div className="bg-amber-50 border-b border-amber-200 p-3 text-center text-amber-800 text-sm">
          Warning: You are logged in with an HR role viewing the candidate portal shell.
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 w-full max-w-5xl mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
