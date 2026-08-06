import { ReactNode } from "react";
import Link from "next/link";

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full flex-col p-8 bg-gray-50 dark:bg-zinc-950 min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Settings
        </h1>
      </div>
      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="w-full lg:w-64 flex-shrink-0">
          <nav className="flex flex-row lg:flex-col space-x-2 lg:space-x-0 lg:space-y-1 overflow-x-auto">
            <Link
              href="/settings/organization"
              className="px-4 py-2 text-sm font-medium hover:bg-gray-200 text-gray-900 dark:text-gray-100 rounded-md dark:hover:bg-zinc-800"
            >
              Organization
            </Link>
            <Link
              href="/settings/users"
              className="px-4 py-2 text-sm font-medium hover:bg-gray-200 text-gray-900 dark:text-gray-100 rounded-md dark:hover:bg-zinc-800"
            >
              Users & Roles
            </Link>
          </nav>
        </aside>
        <main className="flex-1 bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 p-8 min-h-[500px]">
          {children}
        </main>
      </div>
    </div>
  );
}
