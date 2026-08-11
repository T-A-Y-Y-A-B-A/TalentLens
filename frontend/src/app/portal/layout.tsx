"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { Loader2, LogOut, Briefcase, FileText, UserCircle, Bell } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Logo } from "@/components/ui/logo";

export default function CandidatePortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const isPublicRoute = pathname?.includes("/login") || pathname?.includes("/register");

  useEffect(() => {
    if (!isLoading && !user && !isPublicRoute) {
      router.push("/portal/login");
    }
  }, [isLoading, user, isPublicRoute, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-50">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-900" />
      </div>
    );
  }

  // If public route and no user, render bare layout
  if (!user && isPublicRoute) {
    return (
      <div className="min-h-screen bg-zinc-50 flex flex-col">
        <main className="flex-1 w-full mx-auto">
          {children}
        </main>
      </div>
    );
  }

  if (!user && !isPublicRoute) {
    return null; // Will redirect via useEffect
  }

  const isHR = user && ["hr_manager", "hr_admin", "recruiter"].includes(user.role);

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      {/* Top Nav for Candidate */}
      <header className="bg-white border-b border-zinc-200 h-16 sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Logo href="/portal/jobs" size="md" />
          
          <nav className="hidden md:flex items-center gap-6">
            <Link 
              href="/portal/jobs" 
              className={`text-sm font-medium flex items-center gap-2 transition-colors ${pathname?.includes("/jobs") ? "text-indigo-600" : "text-zinc-500 hover:text-zinc-900"}`}
            >
              <Briefcase className="w-4 h-4" />
              Job Board
            </Link>
            <Link 
              href="/portal/applications" 
              className={`text-sm font-medium flex items-center gap-2 transition-colors ${pathname?.includes("/applications") ? "text-indigo-600" : "text-zinc-500 hover:text-zinc-900"}`}
            >
              <FileText className="w-4 h-4" />
              My Applications
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <Link 
                href="/portal/dashboard?tab=notifications" 
                className={`text-zinc-500 hover:text-indigo-600 transition-colors mr-2 flex items-center`}
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
              </Link>
              <Link 
                href="/portal/profile" 
                className={`text-sm font-medium flex items-center gap-2 transition-colors mr-2 ${pathname?.includes("/profile") ? "text-indigo-600" : "text-zinc-500 hover:text-zinc-900"}`}
              >
                <UserCircle className="w-4 h-4" />
                Profile
              </Link>
              <div className="h-4 w-px bg-zinc-200 hidden sm:block"></div>
              <button
                onClick={logout}
                className="text-zinc-500 hover:text-red-600 flex items-center text-sm font-medium transition-colors"
              >
                <LogOut className="h-4 w-4 mr-1.5" />
                <span className="hidden sm:inline-block">Logout</span>
              </button>
            </>
          )}
        </div>
      </header>

      {isHR && (
        <div className="bg-amber-50 border-b border-amber-200 p-3 text-center text-amber-800 text-sm font-medium">
          Warning: You are logged in with an HR role viewing the candidate portal shell.
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 w-full max-w-6xl mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
