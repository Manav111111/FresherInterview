import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
  FiSidebar,
  FiBarChart2,
  FiCheckCircle,
  FiHelpCircle,
  FiAward,
  FiArrowRight,
  FiClock,
  FiCalendar,
} from "react-icons/fi";
import Sidebar from "../components/Sidebar";
import InterviewGraph from "../components/InterviewGraph";
import { getAllInterviews } from "../api/interview.api";
import { logoutUser } from "../api/user.api";
import { useNavigate } from "react-router-dom";

export default function Performance({ user, setUser }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [stats, setStats] = useState({
    totalInterviews: 0,
    totalQuestions: 0,
    completed: 0,
    averageScore: 0,
  });
  const [technicalData, setTechnicalData] = useState([]);
  const [behaviouralData, setBehaviouralData] = useState([]);
  const [technicalCount, setTechnicalCount] = useState(0);
  const [hrCount, setHrCount] = useState(0);
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await getAllInterviews();
        if (response) {
          setStats(
            response.stats || {
              totalInterviews: 0,
              totalQuestions: 0,
              completed: 0,
              averageScore: 0,
            }
          );
          setTechnicalData(response.technicalData || []);
          setBehaviouralData(response.behaviouralData || []);
          setTechnicalCount(response.technicalCount || 0);
          setHrCount(response.hrCount || 0);
          setInterviews(response.interviews || []);
        }
      } catch (err) {
        console.warn("Failed to fetch performance analytics:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
      setUser(null);
      navigate("/");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const hasData = stats.totalInterviews > 0;

  return (
    <div className="bg-[#F8F9FA] min-h-screen text-slate-800 font-sans flex">
      {/* Sidebar */}
      <Sidebar
        user={user}
        onNewInterview={() => navigate("/interview")}
        onLogout={handleLogout}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Area */}
      <motion.main
        className={`flex-1 min-h-screen px-4 sm:px-6 md:px-8 py-5 md:py-6 transition-all duration-300 ${
          collapsed ? "md:ml-[72px]" : "md:ml-[260px]"
        }`}
      >
        {/* Top Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="md:hidden p-2 rounded-xl bg-white border border-slate-200/80 text-slate-600 hover:text-slate-900 transition-colors shadow-xs"
            >
              <FiSidebar size={18} />
            </button>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                Performance &amp; Analytics
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Track your interview readiness score, performance history, and improvement trends.
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-6xl mx-auto space-y-6">
          {hasData ? (
            <>
              {/* Stat Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Interviews */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Total Interviews
                    </p>
                    <h3 className="text-2xl font-extrabold text-slate-900 mt-1">
                      {stats.totalInterviews}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">All time sessions</p>
                  </div>
                  <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <FiBarChart2 size={22} />
                  </div>
                </div>

                {/* Questions Answered */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Questions Solved
                    </p>
                    <h3 className="text-2xl font-extrabold text-slate-900 mt-1">
                      {stats.totalQuestions}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">Across all interviews</p>
                  </div>
                  <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center">
                    <FiHelpCircle size={22} />
                  </div>
                </div>

                {/* Completed */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Completed
                    </p>
                    <h3 className="text-2xl font-extrabold text-slate-900 mt-1">
                      {stats.completed}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">Full reports generated</p>
                  </div>
                  <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <FiCheckCircle size={22} />
                  </div>
                </div>

                {/* Average Score */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Average Score
                    </p>
                    <h3 className="text-2xl font-extrabold text-slate-900 mt-1">
                      {Math.round(stats.averageScore || 0)}/100
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">Overall accuracy</p>
                  </div>
                  <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center">
                    <FiAward size={22} />
                  </div>
                </div>
              </div>

              {/* Performance Graph Card */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      Interview Score Breakdown
                    </h2>
                    <p className="text-xs text-slate-500">
                      Technical vs Behavioral performance trends
                    </p>
                  </div>
                </div>

                <div className="w-full overflow-x-auto">
                  <InterviewGraph
                    technicalData={technicalData}
                    behaviouralData={behaviouralData}
                    technicalCount={technicalCount}
                    hrCount={hrCount}
                  />
                </div>
              </div>

              {/* Past Interviews List */}
              {interviews.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
                  <h2 className="text-base font-bold text-slate-900">
                    Session History
                  </h2>
                  <div className="divide-y divide-slate-100">
                    {interviews.map((itv, idx) => (
                      <div
                        key={idx}
                        className="py-3.5 flex items-center justify-between gap-4 first:pt-0 last:pb-0"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-900">
                              {itv.role || "Software Engineer"}
                            </span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold uppercase">
                              {itv.type || "technical"}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                            <span className="flex items-center gap-1">
                              <FiCalendar size={12} />
                              {itv.created_at
                                ? new Date(itv.created_at).toLocaleDateString()
                                : "Session"}
                            </span>
                            {itv.score !== undefined && (
                              <span className="text-emerald-600 font-semibold">
                                Score: {itv.score}/100
                              </span>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => navigate(`/interview/${itv.id}/report`)}
                          className="px-3.5 py-1.5 rounded-xl bg-slate-50 hover:bg-indigo-50 text-indigo-600 font-semibold text-xs transition flex items-center gap-1"
                        >
                          <span>View Report</span>
                          <FiArrowRight size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Elegant Empty State */
            <div className="rounded-2xl bg-white border border-slate-200/80 p-10 sm:p-14 text-center max-w-2xl mx-auto shadow-xs space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto shadow-xs">
                <FiBarChart2 size={32} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  No interview performance data yet
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
                  Complete your first AI mock interview to unlock comprehensive analytics, score progression, and skill evaluations.
                </p>
              </div>
              <div className="pt-2">
                <button
                  onClick={() => navigate("/interview")}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#4F46E5] hover:bg-[#4338CA] text-white text-xs font-semibold shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <span>Start First Interview</span>
                  <FiArrowRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.main>
    </div>
  );
}
