import { ReactNode } from "react";
import Link from "next/link";

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full flex-col p-8 bg-gray-50 dark:bg-zinc-950 min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Invite Members
        </h1>
      </div>
      <div className="flex flex-col lg:flex-row gap-8">
        <main className="flex-1 bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 p-8 min-h-[500px]">
          {children}
        </main>
      </div>
    </div>
  );
}
