import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://fresherinterview.onrender.com",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
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
