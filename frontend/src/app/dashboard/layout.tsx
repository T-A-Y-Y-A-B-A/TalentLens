"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { Loader2, LayoutDashboard, Users, Briefcase, Settings, LogOut, Menu, Sparkles, BarChart3, Calendar, ShieldAlert, UserPlus } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Jobs", href: "/dashboard/jobs", icon: Briefcase },
  { name: "Candidates", href: "/dashboard/candidates", icon: Users },
  { name: "Interviews", href: "/dashboard/interviews", icon: Calendar },
  { name: "Copilot", href: "/dashboard/copilot", icon: Sparkles },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { name: "Invite Member", href: "/dashboard/invite-member", icon: UserPlus },
];

export default function HRDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, logout, checkRole } = useAuth();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Basic role check - must be logged in and have valid role
  if (!user || !checkRole(["super_admin", "hr_manager", "recruiter", "interviewer"])) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-background p-4 text-center">
        <h1 className="text-2xl font-bold text-destructive mb-2">Access Denied</h1>
        <p className="text-muted-foreground mb-6">
          You do not have permission to access the HR Dashboard.
        </p>
        <Button onClick={logout} variant="outline">
          Sign out and try another account
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-card border-r border-border transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center justify-center border-b border-border px-6">
          <Logo href="/dashboard" size="md" />
        </div>
        
        <div className="flex flex-col justify-between h-[calc(100vh-4rem)]">
          <nav className="mt-6 flex flex-col space-y-1">
            {navItems.filter((item) => {
              if (user?.role === "interviewer") {
                return ["Dashboard", "Interviews"].includes(item.name);
              }
              if (user?.role === "recruiter") {
                return item.name !== "Invite Member";
              }
              return true;
            }).map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center px-4 py-2 text-sm font-medium border-l-[3px] transition-colors ${
                    isActive
                      ? "bg-accent border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                  }`}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 flex-shrink-0 ${
                      isActive ? "text-primary" : "text-muted-foreground"
                    }`}
                  />
                  {item.name}
                </Link>
              );
            })}
            {user?.is_platform_admin && (
              <div className="pt-4 mt-4 border-t border-border px-4">
                <Link
                  href="/admin"
                  className="flex items-center rounded-md px-2 py-2 text-sm font-bold bg-zinc-900 text-white hover:bg-zinc-800"
                >
                  <ShieldAlert className="mr-3 h-5 w-5 flex-shrink-0 text-zinc-300" />
                  Admin Console
                </Link>
              </div>
            )}
          </nav>

          <div className="border-t border-border p-4">
            <div className="flex items-center mb-4">
              <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center text-primary font-bold">
                {user.email.charAt(0).toUpperCase()}
              </div>
              <div className="ml-3 flex-1 overflow-hidden">
                <p className="text-sm font-medium text-foreground truncate">{user.email}</p>
                <p className="text-xs text-muted-foreground capitalize">{user.role.replace("_", " ")}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex w-full items-center rounded-md px-2 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/30 hover:text-foreground"
            >
              <LogOut className="mr-3 h-5 w-5 text-muted-foreground" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header (Mobile mainly) */}
        <header className="flex h-16 items-center justify-between border-b border-border bg-card px-4 sm:px-6 lg:hidden">
          <Logo href="/dashboard" size="sm" />
          <button
            className="text-muted-foreground hover:text-foreground focus:outline-none"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-background p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
