"use client";

import { useState } from "react";
import { Search, Sparkles, Clock, ChevronRight, User, BrainCircuit, ArrowRight, Loader2, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Link from "next/link";

type InterpretedFilter = {
  skills: string[];
  min_experience: string | null;
  certifications: string[];
  keywords: string[];
};

const MOCK_RECENT_QUERIES = [
  "Find Python developers with Kubernetes exp",
  "Senior React engineers in New York",
  "Product Managers with B2B SaaS background"
];

export default function CopilotPage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interpretedFilter, setInterpretedFilter] = useState<InterpretedFilter | null>(null);
  const [candidates, setCandidates] = useState<any[]>([]);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    setError(null);
    try {
      const { apiClient } = await import("@/lib/api/client");
      const res = await apiClient.POST("/api/v1/copilot/query" as any, {
        body: { query: searchQuery } as any
      });
      
      if (res.error) {
        throw new Error(res.error.detail || "Search failed");
      }
      
      setInterpretedFilter(res.data?.interpreted_as as any);
      setCandidates(res.data?.results || []);
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || "An error occurred");
      setHasSearched(false);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleRecentClick = (recentQuery: string) => {
    setQuery(recentQuery);
    performSearch(recentQuery);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center">
          <Sparkles className="mr-2 h-6 w-6 text-indigo-500" />
          AI Copilot
        </h1>
        <p className="text-gray-500 mt-1">
          Use natural language to find exactly the candidates you're looking for.
        </p>
      </div>

      <div className="bg-white border border-zinc-200 shadow-xl rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
            <BrainCircuit size={16} className="text-indigo-600" /> Ask the Copilot
          </label>
          <form onSubmit={handleSearch} className="relative">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Find Python developers with Kubernetes exp..."
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl py-3 px-4 text-zinc-900 font-medium focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            <button type="submit" disabled={!query.trim() || isSearching} className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 rounded-lg w-8 h-8 flex items-center justify-center text-white disabled:opacity-50 hover:bg-indigo-700 transition-colors">
              {isSearching ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
            </button>
          </form>
        </div>

        {hasSearched && interpretedFilter && (
          <div className="pt-4 border-t border-zinc-100 space-y-3 animate-in fade-in duration-500">
            <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Interpreted Filters</p>
            <div className="flex flex-wrap gap-2">
              {interpretedFilter.skills?.map((s, i) => (
                <div key={`skill-${i}`} className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                  Skill: {s} <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                </div>
              ))}
              {interpretedFilter.min_experience && (
                <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                  Experience &ge; {interpretedFilter.min_experience} <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                </div>
              )}
              {interpretedFilter.certifications?.map((s, i) => (
                <div key={`cert-${i}`} className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                  Cert: {s} <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                </div>
              ))}
              {interpretedFilter.keywords?.map((s, i) => (
                <div key={`keyword-${i}`} className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                  Keyword: {s} <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {!hasSearched && !isSearching && (
        <div className="pt-4">
          <h3 className="text-sm font-medium text-gray-500 mb-3 flex items-center">
            <Clock className="mr-2 h-4 w-4" />
            Recent Queries
          </h3>
          <div className="space-y-2">
            {MOCK_RECENT_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => handleRecentClick(q)}
                className="flex items-center text-left w-full p-3 rounded-lg border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50 transition-colors text-sm text-gray-700"
              >
                <Search className="mr-3 h-4 w-4 text-gray-400" />
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-500 text-sm">{error}</div>
      )}

      {hasSearched && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{candidates.length} matching candidates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {candidates.map((cand) => (
                <Card key={cand.candidate_id} className="hover:border-indigo-300 transition-colors">
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold">
                          {cand.name ? cand.name.charAt(0) : "?"}
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{cand.name}</h3>
                          <p className="text-xs text-gray-500">{cand.status}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex flex-wrap gap-1">
                      {cand.skills?.slice(0, 5).map((skill: string, i: number) => (
                        <span key={`skill-cand-${i}`} className="inline-flex text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                          {skill}
                        </span>
                      ))}
                    </div>
                    
                    <div className="mt-5 pt-4 border-t border-gray-100">
                      <Link href={`/dashboard/candidates/${cand.candidate_id}`} className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center">
                        View Profile
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
