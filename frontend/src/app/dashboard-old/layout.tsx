import Link from 'next/link';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-50 flex font-sans">
      <aside className="w-64 bg-white border-r border-zinc-200">
        <div className="p-6 border-b border-zinc-200 flex items-center justify-between">
          <span className="font-bold text-xl tracking-tight text-zinc-900">TalentLens</span>
        </div>
        <nav className="p-4 space-y-1">
          <Link href="/dashboard" className="block px-4 py-2 rounded-md text-sm font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition-colors">
            Overview
          </Link>
          <Link href="/dashboard/organization" className="block px-4 py-2 rounded-md text-sm font-medium text-indigo-600 bg-indigo-50 transition-colors">
            Organization
          </Link>
        </nav>
      </aside>
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
