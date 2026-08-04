"use client";

import { useState, Suspense } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api/client";
import { Loader2, AlertCircle, CheckCircle, Eye, EyeOff } from "lucide-react";
import { useSearchParams } from "next/navigation";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";

const resetSchema = z.object({
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[0-9]/, "Password must contain at least one number"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type ResetFormValues = z.infer<typeof resetSchema>;

function PasswordResetConfirmContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: "", confirmPassword: "" },
  });

  const onSubmit = async (data: ResetFormValues) => {
    if (!token) {
      setApiError("Reset token is missing.");
      return;
    }

    setApiError(null);
    try {
      const { error } = await apiClient.POST("/api/v1/auth/password-reset/confirm", {
        body: { token, new_password: data.password },
      });

      if (error) {
        const errData = error as any;
        setApiError(errData?.detail || "Failed to reset password. The token may be invalid or expired.");
        return;
      }

      setIsSuccess(true);
    } catch (err) {
      setApiError("Failed to connect to the server. Please try again.");
    }
  };

  if (!token) {
    return (
      <div className="w-full text-center">
        <Alert variant="destructive" className="mb-6 text-left">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>Invalid or missing password reset link.</AlertDescription>
        </Alert>
        <Link href="/login" className={buttonVariants({ variant: "outline", className: "w-full" })}>Back to Sign In</Link>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="w-full text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight mb-2">Password Reset!</h1>
        <p className="text-zinc-500 mb-8">
          Your password has been successfully updated.
        </p>
        <Link href="/login" className={buttonVariants({ className: "w-full bg-indigo-600 hover:bg-indigo-700 text-white" })}>Sign In Now</Link>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Create new password</h1>
        <p className="text-zinc-500 mt-2">
          Please enter your new password below.
        </p>
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
          <Label htmlFor="password" className={errors.password ? "text-red-500" : ""}>
            New Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              disabled={isSubmitting}
              className={`pr-10 ${errors.password ? "border-red-500 focus-visible:ring-red-500" : ""}`}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isSubmitting}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && <p className="text-sm text-red-500 mt-1">{errors.password.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className={errors.confirmPassword ? "text-red-500" : ""}>
            Confirm New Password
          </Label>
          <div className="relative">
            <Input
              id="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              placeholder="••••••••"
              disabled={isSubmitting}
              className={`pr-10 ${errors.confirmPassword ? "border-red-500 focus-visible:ring-red-500" : ""}`}
              {...register("confirmPassword")}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              disabled={isSubmitting}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirmPassword && <p className="text-sm text-red-500 mt-1">{errors.confirmPassword.message}</p>}
        </div>

        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Resetting...
            </>
          ) : (
            "Reset Password"
          )}
        </Button>
      </form>
    </div>
  );
}

export default function PasswordResetConfirmPage() {
  return (
    <Suspense fallback={
      <div className="w-full flex flex-col items-center justify-center text-center">
        <Loader2 className="h-12 w-12 animate-spin text-indigo-600 mb-4" />
        <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Loading...</h1>
      </div>
    }>
      <PasswordResetConfirmContent />
    </Suspense>
  );
}
