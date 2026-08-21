'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { User, Briefcase } from 'lucide-react';

export default function UnifiedLoginPage() {
  return (
    <div className="flex min-h-screen w-full bg-[var(--paper)] flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-heading mb-3">
          Sign in to TalentLens
        </h1>
        <p className="text-muted-foreground">
          Choose how you want to sign in to continue.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
        {/* Candidate Card */}
        <Card className="border border-border shadow-sm hover:shadow-md transition-shadow group">
          <CardContent className="p-8 flex flex-col h-full items-center text-center">
            <div className="h-16 w-16 bg-[var(--signal-light)] rounded-full flex items-center justify-center mb-6 transition-transform group-hover:scale-105">
              <div className="h-10 w-10 rounded-full bg-[var(--signal)] flex items-center justify-center text-white shadow-inner">
                <User size={20} strokeWidth={2.5} />
              </div>
            </div>
            
            <h2 className="text-xl font-bold font-heading text-foreground mb-3">
              I'm a candidate
            </h2>
            <p className="text-muted-foreground text-sm mb-8 flex-1">
              Browse open roles, track your applications, and see how you match.
            </p>
            
            <Link href="/portal/login" className="w-full mt-auto">
              <Button className="w-full whitespace-normal h-auto min-h-[3rem] py-3 px-4 bg-[var(--signal)] hover:bg-[var(--signal)]/90 text-white rounded-xl font-semibold">
                Sign in as candidate
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Team Member Card */}
        <Card className="border border-border shadow-sm hover:shadow-md transition-shadow group">
          <CardContent className="p-8 flex flex-col h-full items-center text-center">
            <div className="h-16 w-16 bg-[var(--pass-light)] rounded-full flex items-center justify-center mb-6 transition-transform group-hover:scale-105">
              <div className="h-10 w-10 rounded-full bg-[var(--pass)] flex items-center justify-center text-white shadow-inner">
                <Briefcase size={20} strokeWidth={2.5} />
              </div>
            </div>
            
            <h2 className="text-xl font-bold font-heading text-foreground mb-3">
              I'm on a hiring team
            </h2>
            <p className="text-muted-foreground text-sm mb-8 flex-1">
              Manage jobs, review candidates, and run AI-assisted matching.
            </p>
            
            <Link href="/staff-login" className="w-full mt-auto">
              <Button className="w-full whitespace-normal h-auto min-h-[3rem] py-3 px-4 bg-[var(--pass)] hover:bg-[var(--pass)]/90 text-white rounded-xl font-semibold">
                Sign in as team member
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="mt-12 text-center text-sm text-muted-foreground">
        <Link href="/portal/register" className="font-semibold text-foreground hover:text-[var(--signal)] transition-colors">
          New candidate? Create an account
        </Link>
        <span className="mx-2">·</span>
        <Link href="/register" className="font-semibold text-foreground hover:text-[var(--pass)] transition-colors">
          New team? Request access
        </Link>
      </div>
      </div>
    </div>
  );
}
