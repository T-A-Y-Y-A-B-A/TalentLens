'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { apiClient } from '@/lib/api/client';

const acceptInviteSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type AcceptInviteFormValues = z.infer<typeof acceptInviteSchema>;

function AcceptInviteContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  const [token, setToken] = useState<string | null>(null);
  const [decodedEmail, setDecodedEmail] = useState<string>('');
  const [decodedRole, setDecodedRole] = useState<string>('');
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AcceptInviteFormValues>({
    resolver: zodResolver(acceptInviteSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  useEffect(() => {
    const t = searchParams.get('token');
    if (t) {
      setToken(t);
      try {
        // Simple base64 JWT payload decode for display only (validation happens server-side)
        const payloadStr = atob(t.split('.')[1]);
        const payload = JSON.parse(payloadStr);
        if (payload.email) setDecodedEmail(payload.email);
        if (payload.role) setDecodedRole(payload.role);
      } catch (e) {
        setApiError("Invalid invite token format.");
      }
    } else {
      setApiError("No invite token found in the URL.");
    }
  }, [searchParams]);

  const onSubmit = async (data: AcceptInviteFormValues) => {
    if (!token) return;
    setApiError(null);
    
    try {
      const res = await fetch(`/api/v1/invites/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: token,
          password: data.password
        })
      });
      
      const resData = await res.json();
      
      if (!res.ok) {
        setApiError(resData.detail || 'Failed to accept invite.');
        return;
      }

      // If success, just redirect to login
      router.push('/login?message=invite_accepted');
    } catch (err) {
      setApiError('Failed to connect to the server. Please try again.');
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Accept Invitation</h1>
        <p className="text-zinc-500 mt-2">
          Set a password to complete your account setup.
        </p>
      </div>

      {apiError && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {decodedEmail && !apiError && (
        <div className="mb-6 p-4 rounded-lg bg-zinc-50 border border-zinc-100">
          <div className="text-sm text-zinc-500">Joining as</div>
          <div className="font-medium text-zinc-900">{decodedEmail}</div>
          <div className="text-sm text-zinc-500 mt-2">Role</div>
          <div className="font-medium text-zinc-900 capitalize">{decodedRole.replace('_', ' ')}</div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="password" className={errors.password ? "text-red-500" : ""}>
            Set Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              disabled={isSubmitting || !token}
              className={`pr-10 ${errors.password ? "border-red-500 focus-visible:ring-red-500" : ""}`}
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isSubmitting || !token}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none focus:text-zinc-600"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password ? (
            <p className="text-sm text-red-500 mt-1">{errors.password.message}</p>
          ) : (
             <p className="text-xs text-zinc-500 mt-1">Must be at least 8 characters and contain at least 1 number.</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className={errors.confirmPassword ? "text-red-500" : ""}>
            Confirm Password
          </Label>
          <div className="relative">
            <Input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="••••••••"
              disabled={isSubmitting || !token}
              className={`pr-10 ${errors.confirmPassword ? "border-red-500 focus-visible:ring-red-500" : ""}`}
              {...register('confirmPassword')}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              disabled={isSubmitting || !token}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none focus:text-zinc-600"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirmPassword && <p className="text-sm text-red-500 mt-1">{errors.confirmPassword.message}</p>}
        </div>

        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white mt-4" disabled={isSubmitting || !token}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating Account...
            </>
          ) : (
            'Complete Setup'
          )}
        </Button>
      </form>
    </div>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={<div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>}>
      <AcceptInviteContent />
    </Suspense>
  );
}
