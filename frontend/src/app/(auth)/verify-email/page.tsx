"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import Link from "next/link";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMsg("Verification token is missing from the URL.");
      return;
    }

    const verify = async () => {
      try {
        const { error, response } = await apiClient.POST("/api/v1/auth/verify-email", {
          body: { token }
        });

        if (error) {
          setStatus("error");
          const errData = error as any;
          setErrorMsg(errData?.detail || "Verification failed. The token may be invalid or expired.");
        } else {
          setStatus("success");
        }
      } catch (err) {
        setStatus("error");
        setErrorMsg("Failed to connect to the server.");
      }
    };

    verify();
  }, [token]);

  return (
    <div className="w-full flex flex-col items-center justify-center text-center">
      {status === "loading" && (
        <>
          <Loader2 className="h-12 w-12 animate-spin text-indigo-600 mb-4" />
          <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Verifying your email</h1>
          <p className="text-zinc-500 mt-2">Please wait a moment while we verify your account...</p>
        </>
      )}

      {status === "success" && (
        <>
          <CheckCircle className="h-12 w-12 text-green-600 mb-4" />
          <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Email Verified!</h1>
          <p className="text-zinc-500 mt-2 mb-8">Your account has been successfully verified.</p>
          <Link href="/login" className={buttonVariants({ className: "w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white" })}>Continue to Sign In</Link>
        </>
      )}

      {status === "error" && (
        <>
          <XCircle className="h-12 w-12 text-red-600 mb-4" />
          <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Verification Failed</h1>
          <p className="text-red-500 mt-2 mb-8">{errorMsg}</p>
          <Link href="/login" className={buttonVariants({ variant: "outline", className: "w-full sm:w-auto" })}>Back to Sign In</Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="w-full flex flex-col items-center justify-center text-center">
        <Loader2 className="h-12 w-12 animate-spin text-indigo-600 mb-4" />
        <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Loading...</h1>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
