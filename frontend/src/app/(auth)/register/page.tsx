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
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { apiClient } from '@/lib/api/client';

const registerSchema = z.object({
  fullName: z.string().min(2, 'Full Name must be at least 2 characters'),
  email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
  organizationName: z.string().min(2, 'Organization Name must be at least 2 characters'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
  agreeTerms: z.boolean().refine((val) => val === true, {
    message: 'You must agree to the Terms of Service and Privacy Policy',
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: '',
      email: '',
      organizationName: '',
      password: '',
      confirmPassword: '',
      agreeTerms: false,
    },
  });

  const agreeTerms = watch('agreeTerms');

  const onSubmit = async (data: RegisterFormValues) => {
    setApiError(null);
    try {
      const { data: resData, error, response } = await apiClient.POST('/api/v1/auth/register', {
        body: {
          email: data.email,
          org_name: data.organizationName,
          password: data.password,
        }
      });

      if (error) {
        const errorData = error as any;
        if (errorData && errorData.detail) {
          if (typeof errorData.detail === 'string') {
             setApiError(errorData.detail);
          } else if (Array.isArray(errorData.detail)) {
             setApiError(errorData.detail[0]?.msg || 'Validation error from server');
          } else {
             setApiError('An error occurred during registration.');
          }
        } else {
          setApiError('Registration failed. Please try again.');
        }
        return;
      }

      router.push('/verify-email-sent');
    } catch (err) {
      setApiError('Failed to connect to the server. Please try again.');
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Create your TalentLens account</h1>
        <p className="text-zinc-500 mt-2">Start hiring smarter in minutes.</p>
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
          <Label htmlFor="fullName" className={errors.fullName ? "text-red-500" : ""}>
            Full Name
          </Label>
          <Input
            id="fullName"
            placeholder="John Doe"
            disabled={isSubmitting}
            className={errors.fullName ? "border-red-500 focus-visible:ring-red-500" : ""}
            {...register('fullName')}
          />
          {errors.fullName && <p className="text-sm text-red-500 mt-1">{errors.fullName.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email" className={errors.email ? "text-red-500" : ""}>
            Work Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            disabled={isSubmitting}
            className={errors.email ? "border-red-500 focus-visible:ring-red-500" : ""}
            {...register('email')}
          />
          {errors.email && <p className="text-sm text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="organizationName" className={errors.organizationName ? "text-red-500" : ""}>
            Organization Name
          </Label>
          <Input
            id="organizationName"
            placeholder="Acme Corp"
            disabled={isSubmitting}
            className={errors.organizationName ? "border-red-500 focus-visible:ring-red-500" : ""}
            {...register('organizationName')}
          />
          {errors.organizationName && <p className="text-sm text-red-500 mt-1">{errors.organizationName.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className={errors.password ? "text-red-500" : ""}>
            Password
          </Label>
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
              disabled={isSubmitting}
              className={`pr-10 ${errors.confirmPassword ? "border-red-500 focus-visible:ring-red-500" : ""}`}
              {...register('confirmPassword')}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              disabled={isSubmitting}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none focus:text-zinc-600"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              <span className="sr-only">{showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}</span>
            </button>
          </div>
          {errors.confirmPassword && <p className="text-sm text-red-500 mt-1">{errors.confirmPassword.message}</p>}
        </div>

        <div className="flex items-start space-x-2 pt-2">
          <Checkbox 
            id="agreeTerms" 
            checked={agreeTerms} 
            onCheckedChange={(checked) => setValue('agreeTerms', checked === true, { shouldValidate: true })} 
            disabled={isSubmitting}
          />
          <div className="grid gap-1.5 leading-none">
            <label
              htmlFor="agreeTerms"
              className={`text-sm font-medium leading-none cursor-pointer ${errors.agreeTerms ? 'text-red-500' : 'text-zinc-700'}`}
            >
              I agree to the Terms of Service and Privacy Policy
            </label>
            {errors.agreeTerms && <p className="text-xs text-red-500 mt-1">{errors.agreeTerms.message}</p>}
          </div>
        </div>

        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white mt-4" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating Account...
            </>
          ) : (
            'Create Account'
          )}
        </Button>
      </form>

      <div className="mt-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-200" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-2 text-zinc-500">or</span>
          </div>
        </div>

        <div className="mt-6">
          <a href="/api/v1/auth/oauth/google/login" className="block w-full">
            <Button variant="outline" type="button" className="w-full font-medium" disabled={isSubmitting}>
              <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </Button>
          </a>
        </div>
      </div>

      <p className="mt-8 text-center text-sm text-zinc-600 pb-8">
        Already have an account?{' '}
        <Link href="/login" className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors">
          Sign in
        </Link>
      </p>
    </div>
  );
}
