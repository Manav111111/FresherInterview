import React, { useEffect, useState } from "react";
import { Route, Routes, Navigate } from "react-router-dom";

import Home from "./pages/Home";
import Dashbord from "./pages/Dashbord";
import Roadmap from "./pages/Roadmap";
import Scorer from "./pages/Scorer";
import ResumeBuilder from "./pages/ResumeBuilder";
import Pricing from "./pages/Pricing";
import InterviewStart from "./pages/InterviewStart";
import InterviewPage from "./pages/InterviewPage";
import InterviewReport from "./pages/InterviewReport";
import SolutionVideo from "./pages/SolutionVideo";
import Performance from "./pages/Performance";
import { getCurrentUser } from "./api/user.api";
import ChatbotWidget from "./components/ChatbotWidget";

import { setResume } from "./redux/resumeSlice";
import { getResume } from "./api/resume.api";
import { useDispatch } from "react-redux";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();

  useEffect(() => {
    const getUser = async () => {
      try {
        const token = localStorage.getItem("fresherai_token");
        if (!token) {
          setUser(null);
          setLoading(false);
          return;
        }

        const data = await getCurrentUser();
        if (data?.user) {
          setUser(data.user);
        } else {
          // Authentication failed on backend: clear invalid state, do not set ghost user
          localStorage.removeItem("fresherai_token");
          localStorage.removeItem("fresherai_demo_user");
          setUser(null);
        }
      } catch (err) {
        console.warn("Authentication check notice:", err?.message || err);
        localStorage.removeItem("fresherai_token");
        localStorage.removeItem("fresherai_demo_user");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    getUser();

    const handleSessionExpired = () => {
      setUser(null);
    };
    window.addEventListener("fresherai_session_expired", handleSessionExpired);
    return () => window.removeEventListener("fresherai_session_expired", handleSessionExpired);
  }, []);

  useEffect(() => {
    if (!user) return;
    const fetchResume = async () => {
      try {
        const response = await getResume();
        if (response?.data) {
          dispatch(setResume(response.data));
        }
      } catch (err) {
        console.warn("No active resume stored yet:", err);
      }
    };

    fetchResume();
  }, [user, dispatch]);

  if (loading) {
    return (
      <div className="fixed top-0 left-0 w-full z-[9999]">
        <div className="h-1 bg-white animate-pulse w-full" />
      </div>
    );
  }

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={
            user
              ? <Navigate to="/dashboard" replace />
              : <Home user={user} setUser={setUser} />
          }
        />
        <Route
          path="/dashboard"
          element={
            user
              ? <Dashbord user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/performance"
          element={
            user
              ? <Performance user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/interview"
          element={
            user
              ? <InterviewStart user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/interview/:id"
          element={
            user
              ? <InterviewPage user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/interview/:id/report"
          element={
            user
              ? <InterviewReport user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/resume"
          element={
            user
              ? <ResumeBuilder user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/roadmap"
          element={
            user
              ? <Roadmap user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/scorer"
          element={
            user
              ? <Scorer user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/pricing"
          element={
            user
              ? <Pricing user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
        <Route
          path="/solution-video"
          element={
            user
              ? <SolutionVideo user={user} setUser={setUser} />
              : <Navigate to="/" replace />
          }
        />
      </Routes>

      {/* Global AI Assistant Floating Widget */}
      <ChatbotWidget user={user} />
    </>
  );
}

export default App;