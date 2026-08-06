'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/components/providers/AuthProvider';
import { apiClient } from '@/lib/api/client';

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function CandidateLoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setApiError(null);
    try {
      const { data: resData, error: apiErrorObj } = await apiClient.POST("/api/v1/candidate-portal/login", {
        body: {
          email: data.email,
          password: data.password
        }
      });

      if (apiErrorObj) {
        throw new Error((apiErrorObj as any).detail || "Failed to log in");
      }
      
      if (resData?.access_token) {
        localStorage.setItem("access_token", resData.access_token);
        window.location.href = "/portal/jobs";
      }
    } catch (err: any) {
      setApiError(err.message || 'Failed to connect to the server. Please try again.');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] w-full items-center justify-center p-4">
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-sm border border-zinc-100">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Candidate Login</h1>
          <p className="text-zinc-500 mt-2">Welcome back. Enter your details to continue.</p>
        </div>

        {apiError && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{apiError}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="email" className={errors.email ? "text-red-500" : ""}>
              Email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              disabled={isSubmitting}
              className={errors.email ? "border-red-500 focus-visible:ring-red-500" : ""}
              {...register('email')}
            />
            {errors.email && <p className="text-sm text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" className={errors.password ? "text-red-500" : ""}>
                Password
              </Label>
            </div>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                disabled={isSubmitting}
                className={`pr-10 ${errors.password ? "border-red-500 focus-visible:ring-red-500" : ""}`}
                {...register('password')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isSubmitting}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none focus:text-zinc-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                <span className="sr-only">{showPassword ? 'Hide password' : 'Show password'}</span>
              </button>
            </div>
            {errors.password && <p className="text-sm text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        <p className="mt-8 text-center text-sm text-zinc-600">
          Don&apos;t have an account?{' '}
          <Link href="/portal/register" className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
