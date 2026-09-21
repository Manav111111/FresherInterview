import axios from "axios";

// Automatically resolve API URL: if on localhost use local backend, otherwise use production Render backend
const getBaseURL = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
    if (isLocalhost) {
      return "http://localhost:8000";
    }
    return import.meta.env.VITE_API_URL || "https://fresherinterview.onrender.com";
  }
  return "http://localhost:8000";
};


const api = axios.create({
  baseURL: getBaseURL(),
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 45000,
});

import { auth } from "./firebase";

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fresherai_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    config.headers["x-session-token"] = token;
  }
  return config;
});

// Response interceptor with single token refresh retry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check for 401 Unauthorized on non-retried requests (skip retry on login/logout itself)
    const isAuthRoute = originalRequest?.url?.includes("/api/auth/login") || originalRequest?.url?.includes("/api/auth/logout");
    if (error.response?.status === 401 && originalRequest && !originalRequest._authRetry && !isAuthRoute) {
      originalRequest._authRetry = true;

      // 1. If Firebase Auth has active user, obtain fresh ID token
      const currentUser = auth.currentUser;
      if (currentUser) {
        try {
          const freshIdToken = await currentUser.getIdToken(true);
          if (freshIdToken) {
            try {
              // Attempt to re-establish application backend session
              const loginRes = await axios.post(
                `${api.defaults.baseURL}/api/auth/login`,
                { token: freshIdToken },
                {
                  headers: { "Content-Type": "application/json" },
                  withCredentials: true,
                  timeout: 10000,
                }
              );
              if (loginRes.data?.token) {
                localStorage.setItem("fresherai_token", loginRes.data.token);
                originalRequest.headers.Authorization = `Bearer ${loginRes.data.token}`;
                originalRequest.headers["x-session-token"] = loginRes.data.token;
                return api(originalRequest);
              }
            } catch (_) {
              // If session creation endpoint fails, use fresh ID token directly
              localStorage.setItem("fresherai_token", freshIdToken);
              originalRequest.headers.Authorization = `Bearer ${freshIdToken}`;
              originalRequest.headers["x-session-token"] = freshIdToken;
              return api(originalRequest);
            }
          }
        } catch (refreshErr) {
          console.warn("Authentication refresh error:", refreshErr?.message || refreshErr);
        }
      }

      // Refresh failed or no Firebase session: clear invalid state
      localStorage.removeItem("fresherai_token");
      localStorage.removeItem("fresherai_demo_user");
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("fresherai_session_expired"));
      }
    }

    return Promise.reject(error);
  }
);

export default api;