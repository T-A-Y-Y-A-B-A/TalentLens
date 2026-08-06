"use client";

import { useState } from "react";
import { Search, Sparkles, Clock, ChevronRight, User } from "lucide-react";
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

type MockCandidate = {
  id: string;
  name: string;
  title: string;
  matchScore: number;
  skills: string[];
};

const MOCK_RECENT_QUERIES = [
  "Find Python developers with Kubernetes exp",
  "Senior React engineers in New York",
  "Product Managers with B2B SaaS background"
];

const MOCK_INTERPRETED_FILTER: InterpretedFilter = {
  skills: ["Python", "Kubernetes"],
  min_experience: null,
  certifications: [],
  keywords: []
};

const MOCK_CANDIDATES: MockCandidate[] = [
  { id: "cand-1", name: "Alice Johnson", title: "Backend Engineer", matchScore: 95, skills: ["Python", "Kubernetes", "Docker", "AWS"] },
  { id: "cand-2", name: "Bob Smith", title: "DevOps Engineer", matchScore: 88, skills: ["Python", "Kubernetes", "Terraform", "GCP"] },
  { id: "cand-3", name: "Charlie Davis", title: "Software Developer", matchScore: 82, skills: ["Python", "Go", "Kubernetes"] },
];

export default function CopilotPage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    // Simulate network delay
    setTimeout(() => {
      setIsSearching(false);
      setHasSearched(true);
    }, 800);
  };

  const handleRecentClick = (recentQuery: string) => {
    setQuery(recentQuery);
    setIsSearching(true);
    setTimeout(() => {
      setIsSearching(false);
      setHasSearched(true);
    }, 800);
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

      <Card className="border-indigo-100 shadow-sm">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex gap-4 items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Find Python developers with Kubernetes exp..."
                className="pl-10 h-12 text-lg border-gray-300 focus-visible:ring-indigo-500"
              />
            </div>
            <Button type="submit" disabled={!query.trim() || isSearching} className="h-12 px-6 bg-indigo-600 hover:bg-indigo-700">
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

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

      {hasSearched && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card className="bg-slate-50 border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-500 uppercase tracking-wider">Interpreted As</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <span className="block text-xs text-slate-400 mb-1">Skills</span>
                  <div className="flex flex-wrap gap-1.5">
                    {MOCK_INTERPRETED_FILTER.skills.length > 0 ? (
                      MOCK_INTERPRETED_FILTER.skills.map((s, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {s}
                        </span>
                      ))
                    ) : <span className="text-sm text-slate-500">—</span>}
                  </div>
                </div>
                <div>
                  <span className="block text-xs text-slate-400 mb-1">Min Experience</span>
                  <span className="text-sm text-slate-700 font-medium">{MOCK_INTERPRETED_FILTER.min_experience || "—"}</span>
                </div>
                <div>
                  <span className="block text-xs text-slate-400 mb-1">Certifications</span>
                  <div className="flex flex-wrap gap-1.5">
                    {MOCK_INTERPRETED_FILTER.certifications.length > 0 ? (
                      MOCK_INTERPRETED_FILTER.certifications.map((s, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                          {s}
                        </span>
                      ))
                    ) : <span className="text-sm text-slate-500">—</span>}
                  </div>
                </div>
                <div>
                  <span className="block text-xs text-slate-400 mb-1">Keywords</span>
                  <div className="flex flex-wrap gap-1.5">
                    {MOCK_INTERPRETED_FILTER.keywords.length > 0 ? (
                      MOCK_INTERPRETED_FILTER.keywords.map((s, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-800">
                          {s}
                        </span>
                      ))
                    ) : <span className="text-sm text-slate-500">—</span>}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{MOCK_CANDIDATES.length} matching candidates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {MOCK_CANDIDATES.map((cand) => (
                <Card key={cand.id} className="hover:border-indigo-300 transition-colors">
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold">
                          {cand.name.charAt(0)}
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{cand.name}</h3>
                          <p className="text-xs text-gray-500">{cand.title}</p>
                        </div>
                      </div>
                      <div className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded-full flex items-center">
                        {cand.matchScore}%
                      </div>
                    </div>
                    
                    <div className="mt-4 flex flex-wrap gap-1">
                      {cand.skills.map((skill, i) => (
                        <span key={i} className="inline-flex text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                          {skill}
                        </span>
                      ))}
                    </div>
                    
                    <div className="mt-5 pt-4 border-t border-gray-100">
                      <Link href={`/candidates/${cand.id}`} className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center">
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
