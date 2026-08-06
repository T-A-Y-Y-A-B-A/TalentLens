import createClient, { Middleware } from "openapi-fetch";
import type { paths } from "./schema";

const API_BASE_URL = typeof window !== "undefined" ? "" : "http://127.0.0.1:8000";

export const apiClient = createClient<paths>({
  baseUrl: API_BASE_URL,
});

let isRefreshing = false;
let failedQueue: { resolve: (token: string) => void; reject: (err: any) => void }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token as string);
    }
  });
  failedQueue = [];
};

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    // Only browser handles localStorage
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
    }
    return request;
  },
  
  async onResponse({ request, response }) {
    if (response.status === 401) {
      // If a login or register request fails, let the caller handle it to show validation errors
      if (request.url.includes("/login") || request.url.includes("/register")) {
        return response;
      }

      // Avoid infinite loop if the refresh endpoint itself fails with 401
      if (request.url.includes("/auth/refresh")) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          const path = window.location.pathname;
          if (path !== "/login" && path !== "/" && !path.startsWith("/register") && !path.startsWith("/portal/login") && !path.startsWith("/portal/register")) {
            if (path.startsWith("/portal")) {
              window.location.href = "/portal/login";
            } else {
              window.location.href = "/login";
            }
          }
        }
        return response;
      }

      if (isRefreshing) {
        try {
          const token = await new Promise<string>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          
          const newRequest = new Request(request, {
            headers: new Headers(request.headers)
          });
          newRequest.headers.set("Authorization", `Bearer ${token}`);
          return fetch(newRequest);
        } catch (err) {
          return response;
        }
      }

      isRefreshing = true;

      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
          method: "POST",
          // credentials: "include" tells fetch to send cookies (like refresh_token)
          credentials: "include", 
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          const newToken = data.access_token;
          
          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", newToken);
          }
          
          isRefreshing = false;
          processQueue(null, newToken);

          // Retry the original request
          const newRequest = new Request(request, {
            headers: new Headers(request.headers)
          });
          newRequest.headers.set("Authorization", `Bearer ${newToken}`);
          return fetch(newRequest);
        } else {
          throw new Error("Refresh failed");
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          const path = window.location.pathname;
          if (path !== "/login" && path !== "/" && !path.startsWith("/register") && !path.startsWith("/portal/login") && !path.startsWith("/portal/register")) {
            if (path.startsWith("/portal")) {
              window.location.href = "/portal/login";
            } else {
              window.location.href = "/login";
            }
          }
        }
        return response;
      }
    }

    if (response.status === 403) {
      // We let the UI handle 403s, but we could broadcast an event here if needed
      console.warn("403 Forbidden received from API");
    }

    return response;
  }
};

apiClient.use(authMiddleware);
