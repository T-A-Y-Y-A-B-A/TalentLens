"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";

// For now, no demo org id is needed since candidates are global

export default function CandidateRegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    const phone = formData.get("phone") as string;
    const bio = formData.get("bio") as string;

    try {
      const { data, error: apiError } = await apiClient.POST("/api/v1/candidate-portal/register", {
        body: {
          name,
          email,
          password,
          phone: phone || undefined,
          bio: bio || undefined
        }
      });

      if (apiError) {
        throw new Error((apiError as any).detail || "Failed to register");
      }

      // Redirect to login
      router.push("/candidate/login");
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full items-center justify-center p-4 overflow-y-auto">
      <Card className="w-full max-w-md shadow-lg my-8">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Candidate Registration</CardTitle>
          <CardDescription>
            Create an account to apply for jobs and track your applications.
          </CardDescription>
        </CardHeader>
        <form onSubmit={onSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm flex items-center gap-2 border border-red-100">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" name="name" type="text" required placeholder="Jane Doe" />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input id="email" name="email" type="email" required placeholder="jane@example.com" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number (Optional)</Label>
              <Input id="phone" name="phone" type="tel" placeholder="+1 (555) 000-0000" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bio">Bio / Description (Optional)</Label>
              <textarea 
                id="bio" 
                name="bio" 
                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50" 
                placeholder="Tell us a little bit about yourself and your career goals..."
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" name="password" type="password" required />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button className="w-full" type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Account
            </Button>
            <div className="text-center text-sm text-zinc-500">
              Already have an account?{" "}
              <Link href="/candidate/login" className="text-indigo-600 font-medium hover:underline">
                Sign in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
