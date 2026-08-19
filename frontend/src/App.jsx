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
import { getCurrentUser } from "./api/user.api";

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
        const data = await getCurrentUser();
        if (data?.user) {
          setUser(data.user);
        }
      } catch (err) {
        console.warn("Session check complete:", err);
      } finally {
        setLoading(false);
      }
    };
    getUser();
  }, []);

  useEffect(() => {
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
  }, [dispatch]);




  if (loading) {
    return (
      <div className="fixed top-0 left-0 w-full z-[9999]">
        <div className="h-1 bg-white animate-pulse w-full" />
      </div>
    );
  }

  return (
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
  );
}

export default App;