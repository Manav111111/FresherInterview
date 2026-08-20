import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiSidebar,
  FiBell,
  FiArrowRight,
  FiMessageSquare,
  FiFileText,
  FiStar,
  FiMap,
  FiVideo,
  FiLogOut,
  FiChevronDown,
} from "react-icons/fi";
import { BsStars } from "react-icons/bs";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";
import { getAllInterviews } from "../api/interview.api";
import { logoutUser } from "../api/user.api";

export default function Dashboard({ user, setUser }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();
  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "FC";

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await getAllInterviews();
        if (response) {
          const rawInterviews = response.interviews || [];
          setInterviews(rawInterviews);
        }
      } catch (err) {
        console.warn("Failed to load interview history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
      setUser(null);
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return (
    <div className="bg-[#F8F9FB] min-h-screen text-slate-800 font-sans flex">
      {/* ── Left Sidebar ── */}
      <Sidebar
        user={user}
        onNewInterview={() => navigate("/interview")}
        onLogout={handleLogout}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* ── Main Content Area ── */}
      <motion.main
        className={`flex-1 min-h-screen px-4 sm:px-6 md:px-8 py-5 md:py-6 transition-all duration-300 ${
          collapsed ? "md:ml-[72px]" : "md:ml-[260px]"
        }`}
      >
        {/* ── Top Header Bar ── */}
        <div className="flex items-center justify-between mb-6">
          {/* Mobile hamburger */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="md:hidden p-2 rounded-xl bg-white border border-slate-200/80 text-slate-600 hover:text-slate-900 transition-colors shadow-xs"
            >
              <FiSidebar size={18} />
            </button>
          </div>

          {/* Right Header: Notifications & Profile */}
          <div className="flex items-center gap-3 ml-auto">
            {/* Notification Bell */}
            <div className="relative">
              <button
                className="w-10 h-10 rounded-full bg-white border border-slate-200/80 hover:bg-slate-50 flex items-center justify-center text-slate-600 transition shadow-xs"
                title="Notifications"
              >
                <FiBell size={17} />
                <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[9px] font-bold flex items-center justify-center border-2 border-white">
                  2
                </span>
              </button>
            </div>

            {/* Profile Avatar Dropdown */}
            <div className="relative">
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2 p-1 pl-1.5 pr-2.5 rounded-full bg-white border border-slate-200/80 hover:bg-slate-50 transition shadow-xs"
              >
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name}
                    className="w-8 h-8 rounded-full object-cover border border-slate-200"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold text-xs shadow-xs">
                    {initials}
                  </div>
                )}
                <FiChevronDown size={14} className="text-slate-400" />
              </button>

              <AnimatePresence>
                {profileDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-52 bg-white rounded-2xl border border-slate-200/80 shadow-xl p-2 z-50 text-xs text-slate-700"
                  >
                    <div className="px-3 py-2 border-b border-slate-100 mb-1">
                      <p className="font-bold text-slate-900 truncate">
                        {user?.name ?? "Fresher Candidate"}
                      </p>
                      <p className="text-[10px] text-slate-400 truncate">
                        {user?.email ?? "candidate@fresher.ai"}
                      </p>
                    </div>

                    <button
                      onClick={() => {
                        navigate("/pricing");
                        setProfileDropdownOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-purple-50 hover:text-purple-700 transition text-left"
                    >
                      <BsStars size={14} className="text-purple-600" />
                      <span>Upgrade &amp; Coins</span>
                    </button>

                    <button
                      onClick={() => {
                        handleLogout();
                        setProfileDropdownOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-red-50 text-red-600 transition text-left"
                    >
                      <FiLogOut size={14} />
                      <span>Log out</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        <div className="max-w-6xl mx-auto space-y-8">
          {/* ── 1. Hero Section ── */}
          <div className="relative rounded-[28px] bg-gradient-to-r from-[#EEF2FF]/80 via-[#F5F3FF]/90 to-[#FAF5FF] border border-indigo-100/90 p-6 sm:p-8 md:p-10 shadow-[0_4px_24px_rgba(79,70,229,0.04)] overflow-hidden flex flex-col md:flex-row items-center justify-between gap-8">
            {/* Left Column Content */}
            <div className="flex-1 max-w-xl z-10">
              {/* Badge */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/90 backdrop-blur-md border border-indigo-100 text-xs font-semibold text-slate-700 shadow-xs mb-4">
                <span>👋 Welcome back!</span>
              </div>

              {/* Title */}
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-[1.15] mb-3">
                Ready to{" "}
                <span className="text-[#4F46E5] bg-gradient-to-r from-[#4F46E5] to-[#7C3AED] bg-clip-text text-transparent">
                  ace
                </span>{" "}
                your next interview?
              </h1>

              {/* Subtitle */}
              <p className="text-slate-600 text-xs sm:text-sm font-normal leading-relaxed mb-6">
                Practice with AI, improve your answers, and get personalised feedback.
              </p>

              {/* Action Button & Social Proof */}
              <div className="flex flex-wrap items-center gap-4 sm:gap-6">
                <button
                  onClick={() => navigate("/interview")}
                  className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#4F46E5] hover:bg-[#4338CA] text-white text-xs sm:text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <span>Start Practicing</span>
                  <FiArrowRight size={15} />
                </button>

                {/* Social Proof Avatars */}
                <div className="flex items-center gap-2.5">
                  <div className="flex -space-x-2">
                    <img
                      className="w-7 h-7 rounded-full border-2 border-white object-cover"
                      src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&auto=format&fit=crop&q=80"
                      alt="Student"
                    />
                    <img
                      className="w-7 h-7 rounded-full border-2 border-white object-cover"
                      src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&auto=format&fit=crop&q=80"
                      alt="Student"
                    />
                    <img
                      className="w-7 h-7 rounded-full border-2 border-white object-cover"
                      src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&auto=format&fit=crop&q=80"
                      alt="Student"
                    />
                  </div>
                  <span className="text-[11px] font-medium text-slate-500">
                    <strong className="text-slate-700 font-bold">10K+</strong> students practicing every day
                  </span>
                </div>
              </div>
            </div>

            {/* Right Column: 3D AI Robot Illustration Area */}
            <div className="relative w-full max-w-[280px] sm:max-w-[320px] aspect-square flex items-center justify-center shrink-0">
              {/* Soft purple radial glow */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-300/30 to-purple-400/30 blur-2xl transform scale-90" />

              {/* Floating Code Badge */}
              <motion.div
                animate={{ y: [-4, 6, -4] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-4 left-2 z-20 w-11 h-11 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-500/25 font-mono font-bold text-sm"
              >
                &lt;/&gt;
              </motion.div>

              {/* Floating Orange Chat Badge */}
              <motion.div
                animate={{ y: [6, -6, 6] }}
                transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-8 right-2 z-20 w-11 h-11 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-lg shadow-orange-500/25"
              >
                <FiMessageSquare size={18} />
              </motion.div>

              {/* 3D Robot Mascot SVG */}
              <div className="relative z-10 w-48 h-48 sm:w-56 sm:h-56 flex items-center justify-center">
                <svg
                  viewBox="0 0 200 200"
                  className="w-full h-full drop-shadow-xl"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Base Body */}
                  <ellipse cx="100" cy="165" rx="42" ry="18" fill="#CBD5E1" opacity="0.5" />
                  <rect x="65" y="110" width="70" height="50" rx="20" fill="url(#bot_body)" />
                  {/* Chest Screen */}
                  <rect x="75" y="122" width="50" height="24" rx="10" fill="#0F172A" />
                  <circle cx="90" cy="134" r="3" fill="#60A5FA" />
                  <circle cx="100" cy="134" r="3" fill="#34D399" />
                  <circle cx="110" cy="134" r="3" fill="#F472B6" />
                  {/* Neck */}
                  <rect x="90" y="98" width="20" height="15" rx="4" fill="#94A3B8" />
                  {/* Head */}
                  <rect x="52" y="45" width="96" height="60" rx="24" fill="url(#bot_head)" stroke="#FFFFFF" strokeWidth="3" />
                  {/* Ears / Headset */}
                  <circle cx="48" cy="75" r="9" fill="#818CF8" />
                  <circle cx="152" cy="75" r="9" fill="#818CF8" />
                  {/* Face Screen */}
                  <rect x="62" y="55" width="76" height="40" rx="16" fill="#0F172A" />
                  {/* Cute Eyes */}
                  <circle cx="83" cy="74" r="7" fill="#60A5FA" />
                  <circle cx="85" cy="72" r="2.5" fill="#FFFFFF" />
                  <circle cx="117" cy="74" r="7" fill="#60A5FA" />
                  <circle cx="119" cy="72" r="2.5" fill="#FFFFFF" />
                  {/* Smile */}
                  <path d="M93 83C96 86 104 86 107 83" stroke="#60A5FA" strokeWidth="2.5" strokeLinecap="round" />
                  {/* Antenna */}
                  <line x1="100" y1="45" x2="100" y2="30" stroke="#818CF8" strokeWidth="3" strokeLinecap="round" />
                  <circle cx="100" cy="27" r="5" fill="#A78BFA" />

                  {/* Gradients */}
                  <defs>
                    <linearGradient id="bot_head" x1="52" y1="45" x2="148" y2="105" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#F8FAFC" />
                      <stop offset="1" stopColor="#E2E8F0" />
                    </linearGradient>
                    <linearGradient id="bot_body" x1="65" y1="110" x2="135" y2="160" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#FFFFFF" />
                      <stop offset="1" stopColor="#E2E8F0" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>

          {/* ── 2. Start an Interview Section ── */}
          <div className="space-y-3">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
                <span>🚀</span>
                <span>Start an Interview</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Choose your interview type and begin your AI-powered practice
              </p>
            </div>

            {/* 3 Horizontal Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Technical Interview Card */}
              <motion.div
                whileHover={{ y: -3, scale: 1.01 }}
                onClick={() => navigate("/interview", { state: { defaultType: "technical" } })}
                className="group relative bg-white rounded-2xl border border-indigo-100/90 hover:border-indigo-300 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div className="flex items-start gap-3.5 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-mono font-bold text-base shadow-sm shrink-0">
                    &lt;/&gt;
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                      Technical Interview
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Practice DSA, web development, CS fundamentals and technical concepts.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <div className="w-8 h-8 rounded-full border border-slate-200 group-hover:border-indigo-500 group-hover:bg-indigo-600 group-hover:text-white text-slate-400 flex items-center justify-center transition-all shadow-2xs">
                    <FiArrowRight size={14} />
                  </div>
                </div>
              </motion.div>

              {/* HR Interview Card */}
              <motion.div
                whileHover={{ y: -3, scale: 1.01 }}
                onClick={() => navigate("/interview", { state: { defaultType: "hr" } })}
                className="group relative bg-white rounded-2xl border border-orange-100/90 hover:border-orange-300 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div className="flex items-start gap-3.5 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-sm shrink-0">
                    <svg viewBox="0 0 24 24" className="w-6 h-6 fill-none stroke-current stroke-2">
                      <circle cx="10" cy="8" r="4" />
                      <path d="M4 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
                      <path d="M19 8c0 1.5-0.7 2.8-1.8 3.5" />
                      <path d="M21 5c0 3-1.5 5.5-3.5 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-orange-600 transition-colors">
                      HR Interview
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Prepare for behavioural, communication and HR questions.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <div className="w-8 h-8 rounded-full border border-slate-200 group-hover:border-orange-500 group-hover:bg-orange-500 group-hover:text-white text-slate-400 flex items-center justify-center transition-all shadow-2xs">
                    <FiArrowRight size={14} />
                  </div>
                </div>
              </motion.div>

              {/* Custom Interview Card */}
              <motion.div
                whileHover={{ y: -3, scale: 1.01 }}
                onClick={() => navigate("/interview", { state: { defaultType: "custom" } })}
                className="group relative bg-white rounded-2xl border border-emerald-100/90 hover:border-emerald-300 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div className="flex items-start gap-3.5 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-500 text-white flex items-center justify-center shadow-sm shrink-0">
                    <BsStars size={22} />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
                      Custom Interview
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Create an interview based on your role, skills and experience.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <div className="w-8 h-8 rounded-full border border-slate-200 group-hover:border-emerald-500 group-hover:bg-emerald-500 group-hover:text-white text-slate-400 flex items-center justify-center transition-all shadow-2xs">
                    <FiArrowRight size={14} />
                  </div>
                </div>
              </motion.div>
            </div>
          </div>

          {/* ── 3. Prepare Smarter Section ── */}
          <div className="space-y-3">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
                <span>✨</span>
                <span>Prepare smarter</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Use AI-powered tools to level up your interview preparation
              </p>
            </div>

            {/* 4 Tool Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Resume Builder */}
              <motion.div
                whileHover={{ y: -3 }}
                onClick={() => navigate("/resume")}
                className="group bg-white rounded-2xl border border-slate-200/80 hover:border-indigo-200 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-indigo-500 text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform shadow-xs">
                    <FiFileText size={20} />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">Resume Builder</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Build a professional resume with AI guidance.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-indigo-600 group-hover:translate-x-0.5 transition-transform">
                  <span>Explore</span>
                  <FiArrowRight size={13} />
                </div>
              </motion.div>

              {/* Resume Score */}
              <motion.div
                whileHover={{ y: -3 }}
                onClick={() => navigate("/scorer")}
                className="group bg-white rounded-2xl border border-slate-200/80 hover:border-orange-200 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-orange-500 text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform shadow-xs">
                    <svg viewBox="0 0 24 24" className="w-5 h-5 fill-none stroke-current stroke-2">
                      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                      <circle cx="12" cy="12" r="4" />
                      <path d="M12 12l2.5-2.5" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">Resume Score</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Analyse your resume and discover what to improve.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-orange-600 group-hover:translate-x-0.5 transition-transform">
                  <span>Explore</span>
                  <FiArrowRight size={13} />
                </div>
              </motion.div>

              {/* Roadmap Builder */}
              <motion.div
                whileHover={{ y: -3 }}
                onClick={() => navigate("/roadmap")}
                className="group bg-white rounded-2xl border border-slate-200/80 hover:border-emerald-200 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-emerald-500 text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform shadow-xs">
                    <FiMap size={20} />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">Roadmap Builder</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Get a personalised learning roadmap for your target role.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-emerald-600 group-hover:translate-x-0.5 transition-transform">
                  <span>Explore</span>
                  <FiArrowRight size={13} />
                </div>
              </motion.div>

              {/* Solution Video */}
              <motion.div
                whileHover={{ y: -3 }}
                onClick={() => navigate("/solution-video")}
                className="group bg-white rounded-2xl border border-slate-200/80 hover:border-blue-200 p-5 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-blue-500 text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform shadow-xs">
                    <FiVideo size={20} />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">Solution Video</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Understand interview and coding solutions visually.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-blue-600 group-hover:translate-x-0.5 transition-transform">
                  <span>Explore</span>
                  <FiArrowRight size={13} />
                </div>
              </motion.div>
            </div>
          </div>

          {/* ── 4. Recent Activity / Premium Empty State ── */}
          {interviews.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900">
                    Continue your preparation
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Recent interviews and performance reports
                  </p>
                </div>
                <button
                  onClick={() => navigate("/performance")}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <span>View All</span>
                  <FiArrowRight size={13} />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {interviews.slice(0, 4).map((itv, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded-2xl border border-slate-200/80 p-4 flex items-center justify-between gap-3 shadow-xs hover:border-indigo-200 transition"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-slate-900">
                          {itv.role || "Software Engineer"}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold uppercase">
                          {itv.type || "technical"}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {itv.created_at ? new Date(itv.created_at).toLocaleDateString() : "Recent Session"}
                      </p>
                    </div>

                    <button
                      onClick={() => navigate(`/interview/${itv.id}/report`)}
                      className="px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-600 font-semibold text-xs hover:bg-indigo-100 transition"
                    >
                      View Report
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Premium Empty State from Reference UI */
            <div className="rounded-2xl bg-gradient-to-r from-[#F5F3FF] via-[#EEF2FF] to-[#F8F9FA] border border-indigo-100/90 p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs">
              {/* Left: Cute 3D Backpack Vector */}
              <div className="w-28 h-28 sm:w-32 sm:h-32 flex items-center justify-center shrink-0">
                <svg
                  viewBox="0 0 120 120"
                  className="w-full h-full drop-shadow-md"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Backpack Body */}
                  <rect x="25" y="35" width="70" height="70" rx="20" fill="url(#bp_grad)" />
                  {/* Front Pocket */}
                  <rect x="35" y="65" width="50" height="32" rx="10" fill="#A5B4FC" opacity="0.9" />
                  <line x1="45" y1="75" x2="75" y2="75" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" />
                  {/* Top Handle */}
                  <path d="M48 35V24C48 20.6863 50.6863 18 54 18H66C69.3137 18 72 20.6863 72 24V35" stroke="#818CF8" strokeWidth="4" strokeLinecap="round" />
                  {/* Sparkles */}
                  <circle cx="100" cy="25" r="3" fill="#FBBF24" />
                  <circle cx="15" cy="50" r="2.5" fill="#818CF8" />

                  <defs>
                    <linearGradient id="bp_grad" x1="25" y1="35" x2="95" y2="105" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#C7D2FE" />
                      <stop offset="1" stopColor="#818CF8" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              {/* Right: Message & Button */}
              <div className="flex-1 text-center md:text-left">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-1">
                  Your interview journey starts here
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mb-4 max-w-md">
                  Complete your first AI interview and track your improvement over time.
                </p>
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