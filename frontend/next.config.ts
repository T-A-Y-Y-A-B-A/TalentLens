import type { NextConfig } from "next";

// BACKEND_URL is a server-side-only env var used by Next.js rewrites at runtime.
// It is NOT prefixed with NEXT_PUBLIC_ so it won't be baked into the client bundle.
// In Docker this should point to the backend container (e.g. http://backend:8000).
// For local dev outside Docker, it falls back to http://127.0.0.1:8000.
const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
