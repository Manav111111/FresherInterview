import React, { useEffect, useState, lazy, Suspense } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import { useDispatch } from "react-redux";

// Eager load Home so the public landing page renders with zero additional network hops
import Home from "./pages/Home";

// Route-level code-splitting: heavy modules are loaded on demand
const Dashbord = lazy(() => import("./pages/Dashbord"));
const Roadmap = lazy(() => import("./pages/Roadmap"));
const Scorer = lazy(() => import("./pages/Scorer"));
const ResumeBuilder = lazy(() => import("./pages/ResumeBuilder"));
const Pricing = lazy(() => import("./pages/Pricing"));
const InterviewStart = lazy(() => import("./pages/InterviewStart"));
const InterviewPage = lazy(() => import("./pages/InterviewPage"));
const InterviewReport = lazy(() => import("./pages/InterviewReport"));
const SolutionVideo = lazy(() => import("./pages/SolutionVideo"));
const Performance = lazy(() => import("./pages/Performance"));
const ChatbotWidget = lazy(() => import("./components/ChatbotWidget"));

import BrandedLoading from "./components/BrandedLoading";
import ErrorBoundary from "./components/ErrorBoundary";
import { getCurrentUser } from "./api/user.api";
import { setResume } from "./redux/resumeSlice";
import { getResume } from "./api/resume.api";

/**
 * Route protection wrapper:
 * - If user session is actively verifying and no cached user exists, shows branded loading state
 * - If verification completes and user is null, securely redirects to "/"
 * - Otherwise renders the protected page immediately
 */
function ProtectedRoute({ user, authLoading, children }) {
  if (authLoading && !user) {
    return <BrandedLoading message="Verifying secure session..." />;
  }
  if (!user) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  // Synchronous user hydration from localStorage to eliminate FCP delay
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("fresherai_demo_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  // Auth is only pending if a token exists and we don't have a hydrated user yet
  const [authLoading, setAuthLoading] = useState(() => {
    const hasToken = typeof window !== "undefined" && !!localStorage.getItem("fresherai_token");
    const hasCachedUser = typeof window !== "undefined" && !!localStorage.getItem("fresherai_demo_user");
    return hasToken && !hasCachedUser;
  });

  const dispatch = useDispatch();

  useEffect(() => {
    let isMounted = true;

    const verifySession = async () => {
      const token = localStorage.getItem("fresherai_token");
      if (!token) {
        if (isMounted) {
          setUser(null);
          setAuthLoading(false);
        }
        return;
      }

      try {
        // Fast non-blocking verification with 6000ms timeout
        const data = await getCurrentUser({ timeout: 6000 });
        if (!isMounted) return;

        if (data?.user) {
          setUser(data.user);
          localStorage.setItem("fresherai_demo_user", JSON.stringify(data.user));
        } else {
          // Token rejected or expired on backend
          localStorage.removeItem("fresherai_token");
          localStorage.removeItem("fresherai_demo_user");
          setUser(null);
        }
      } catch (err) {
        console.warn("Background authentication sync notice:", err?.message || err);
      } finally {
        if (isMounted) {
          setAuthLoading(false);
        }
      }
    };

    verifySession();

    const handleSessionExpired = () => {
      setUser(null);
      setAuthLoading(false);
    };
    window.addEventListener("fresherai_session_expired", handleSessionExpired);
    return () => {
      isMounted = false;
      window.removeEventListener("fresherai_session_expired", handleSessionExpired);
    };
  }, []);

  // Fetch active resume non-blockingly once user is confirmed
  useEffect(() => {
    if (!user) return;
    let isMounted = true;

    const fetchResume = async () => {
      try {
        const response = await getResume();
        if (isMounted && response?.data) {
          dispatch(setResume(response.data));
        }
      } catch (err) {
        console.warn("No active resume stored yet:", err);
      }
    };

    fetchResume();
    return () => {
      isMounted = false;
    };
  }, [user, dispatch]);

  return (
    <ErrorBoundary>
      <Suspense fallback={<BrandedLoading message="Loading Fresher.AI..." />}>
        <Routes>
          {/* Public Home route: renders immediately without blocking on authentication */}
          <Route
            path="/"
            element={
              user ? <Navigate to="/dashboard" replace /> : <Home user={user} setUser={setUser} />
            }
          />

          {/* Public Pricing route */}
          <Route
            path="/pricing"
            element={<Pricing user={user} setUser={setUser} />}
          />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <Dashbord user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/performance"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <Performance user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <InterviewStart user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/:id"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <InterviewPage user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/:id/report"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <InterviewReport user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/resume"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <ResumeBuilder user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmap"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <Roadmap user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/scorer"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <Scorer user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/solution-video"
            element={
              <ProtectedRoute user={user} authLoading={authLoading}>
                <SolutionVideo user={user} setUser={setUser} />
              </ProtectedRoute>
            }
          />

          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Global AI Assistant Floating Widget (Lazy loaded) */}
        <Suspense fallback={null}>
          <ChatbotWidget user={user} />
        </Suspense>
      </Suspense>
    </ErrorBoundary>
  );
}

export default App;