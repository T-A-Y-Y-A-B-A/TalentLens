"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api/client";
import { Loader2, AlertCircle, CheckCircle } from "lucide-react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";

const requestSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
});

type RequestFormValues = z.infer<typeof requestSchema>;

export default function PasswordResetRequestPage() {
  const [isSuccess, setIsSuccess] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RequestFormValues>({
    resolver: zodResolver(requestSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (data: RequestFormValues) => {
    setApiError(null);
    try {
      const { error } = await apiClient.POST("/api/v1/auth/password-reset/request", {
        body: { email: data.email },
      });

      if (error) {
        setApiError("An unexpected error occurred. Please try again.");
        return;
      }

      setIsSuccess(true);
    } catch (err) {
      setApiError("Failed to connect to the server. Please try again.");
    }
  };

  if (isSuccess) {
    return (
      <div className="w-full text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight mb-2">Check your email</h1>
        <p className="text-zinc-500 mb-8">
          If an account exists for that email, we have sent password reset instructions.
        </p>
        <Link href="/login" className={buttonVariants({ variant: "outline", className: "w-full" })}>Back to Sign In</Link>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Reset your password</h1>
        <p className="text-zinc-500 mt-2">
          Enter your email address and we'll send you a link to reset your password.
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
          <Label htmlFor="email" className={errors.email ? "text-red-500" : ""}>
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            disabled={isSubmitting}
            className={errors.email ? "border-red-500 focus-visible:ring-red-500" : ""}
            {...register("email")}
          />
          {errors.email && <p className="text-sm text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Sending Link...
            </>
          ) : (
            "Send Reset Link"
          )}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-zinc-600">
        Remember your password?{" "}
        <Link href="/login" className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors">
          Sign in
        </Link>
      </p>
    </div>
  );
}
