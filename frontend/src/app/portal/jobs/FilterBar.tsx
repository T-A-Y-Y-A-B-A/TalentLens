"use client";

import { Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { useState } from "react";

export type JobBoardFilters = {
  search: string;
  work_type: string | null;
  location: string;
  salary_min: number | null;
  sort_by_match: boolean;
};

export function FilterBar({
  filters,
  onChange,
  hasResume,
  resultCount,
}: {
  filters: JobBoardFilters;
  onChange: (f: JobBoardFilters) => void;
  hasResume: boolean;
  resultCount: number;
}) {
  return (
    <div className="border-b border-slate-800 bg-slate-900/50 p-4">
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search roles, keywords..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="w-full rounded-md border border-slate-700 bg-slate-950 py-2 pl-9 pr-4 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <select
            value={filters.work_type || ""}
            onChange={(e) => onChange({ ...filters, work_type: e.target.value || null })}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Any Work Type</option>
            <option value="REMOTE">Remote</option>
            <option value="HYBRID">Hybrid</option>
            <option value="ONSITE">Onsite</option>
          </select>
          
          {hasResume && (
            <button
              onClick={() => onChange({ ...filters, sort_by_match: !filters.sort_by_match })}
              className={`flex items-center gap-1 rounded-md border px-2 py-1.5 text-xs transition-colors ${
                filters.sort_by_match 
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-400" 
                  : "border-slate-700 bg-slate-950 text-slate-400 hover:text-slate-300"
              }`}
            >
              <Sparkles className="h-3 w-3" /> Best Match
            </button>
          )}
        </div>
        <span className="text-xs text-slate-500">{resultCount} results</span>
      </div>
    </div>
  );
}
