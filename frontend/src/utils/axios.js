import axios from "axios";

// Automatically resolve API URL: if on any hosted domain (e.g. Vercel / mobile), always use Render backend
const getBaseURL = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
    if (!isLocalhost) {
      return "https://fresherinterview.onrender.com";
    }
  }
  return import.meta.env.VITE_API_URL || "http://localhost:8000";
};

const api = axios.create({
  baseURL: getBaseURL(),
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 45000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fresherai_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    config.headers["x-session-token"] = token;
  }
  return config;
});

export default api;