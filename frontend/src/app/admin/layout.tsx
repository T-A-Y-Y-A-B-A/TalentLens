"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { Loader2, LayoutDashboard, Building2, Activity, ShieldAlert, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";

const navItems = [
  { name: "Overview", href: "/admin", icon: LayoutDashboard },
  { name: "Organizations", href: "/admin/organizations", icon: Building2 },
  { name: "AI Usage", href: "/admin/usage", icon: Activity },
  { name: "Audit Logs", href: "/admin/audit-logs", icon: ShieldAlert },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  // Role check - must be platform admin
  useEffect(() => {
    if (!isLoading && user && !user.is_platform_admin) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || (user && !user.is_platform_admin)) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-50">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-900" />
      </div>
    );
  }

  if (!user) {
    return null; // AuthProvider will handle redirect to /login
  }

  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 border-r border-zinc-200 bg-zinc-900 text-zinc-300">
        <div className="flex h-16 items-center px-6 border-b border-zinc-800">
          <Logo href="/admin" size="md" className="[&>span]:text-white" />
        </div>
        
        <div className="flex flex-col justify-between h-[calc(100vh-4rem)]">
          <nav className="mt-6 px-4 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-600 text-white"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  }`}
                >
                  <item.icon className={`mr-3 h-5 w-5 shrink-0 ${isActive ? "text-indigo-200" : "text-zinc-500"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-zinc-800">
            <div className="flex items-center mb-4 px-2">
              <div className="h-8 w-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold border border-zinc-700">
                {user.email.charAt(0).toUpperCase()}
              </div>
              <div className="ml-3 flex-1 overflow-hidden">
                <p className="text-sm font-medium text-zinc-200 truncate">{user.email}</p>
                <p className="text-xs text-zinc-500">Super Admin</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex w-full items-center rounded-md px-3 py-2 text-sm font-medium text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
            >
              <LogOut className="mr-3 h-5 w-5 shrink-0" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="h-16 border-b border-zinc-200 bg-white px-8 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900">Platform Console</h2>
          <div className="text-sm text-zinc-500">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
