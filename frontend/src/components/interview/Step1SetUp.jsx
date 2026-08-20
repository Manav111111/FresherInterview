import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiArrowLeft,
  FiArrowRight,
  FiBriefcase,
  FiCheck,
  FiCheckCircle,
  FiFileText,
  FiUploadCloud,
  FiBarChart2,
  FiMessageSquare,
  FiZap,
} from "react-icons/fi";
import { BsStars, BsLightbulb } from "react-icons/bs";
import { HiSparkles } from "react-icons/hi";
import { GiArtificialHive } from "react-icons/gi";
import { useDispatch, useSelector } from "react-redux";
import { setResume } from "../../redux/resumeSlice";
import { useNavigate, useLocation } from "react-router-dom";
import { startInterview } from "../../api/interview.api";
import { uploadResume as apiUploadResume } from "../../api/resume.api";
import { useCoins } from "../../api/user.api";

function Step1SetUp({ user, setUser }) {
  const dispatch = useDispatch();
  const location = useLocation();
  const { resume } = useSelector((state) => state.resume);

  const initialType = location.state?.defaultType === "hr" ? "hr" : "technical";
  const [role, setRole] = useState(location.state?.defaultRole || "Backend Developer");
  const [type, setType] = useState(initialType);
  const [useResume, setUseResume] = useState(!!resume);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    if (location.state?.defaultType === "hr") {
      setType("hr");
    } else if (location.state?.defaultType === "technical") {
      setType("technical");
    }
    if (location.state?.defaultRole) {
      setRole(location.state.defaultRole);
    }
  }, [location.state]);

  useEffect(() => {
    setUseResume(!!resume);
    if (resume?.role && !location.state?.defaultRole) {
      setRole(resume.role);
    }
  }, [resume]);

  const uploadResume = async () => {
    if (!file) return;
    try {
      setUploading(true);
      const coinResponse = await useCoins({ coins: 10, action: "resume-score" });
      if (coinResponse?.interviewCoin !== undefined) {
        setUser((prev) => ({ ...prev, interviewCoin: coinResponse.interviewCoin }));
      }
      const formData = new FormData();
      formData.append("resume", file);
      const response = await apiUploadResume(formData);
      if (response?.data) {
        dispatch(setResume(response.data));
        setShowUploadModal(false);
      }
    } catch (error) {
      console.error("Resume upload error:", error);
      alert(error.response?.data?.detail || error.response?.data?.message || "Failed to upload resume");
    } finally {
      setUploading(false);
    }
  };

  const start = async () => {
    if (!role.trim()) {
      alert("Please enter a target job role");
      return;
    }

    try {
      setStarting(true);
      const coinResponse = await useCoins({ coins: 50, action: "interview" });
      if (coinResponse?.interviewCoin !== undefined) {
        setUser((prev) => ({ ...prev, interviewCoin: coinResponse.interviewCoin }));
      }

      const response = await startInterview({ role: role.trim(), type, useResume, resume });
      if (response?.interviewId) {
        navigate(`/interview/${response.interviewId}`);
      } else {
        throw new Error("Failed to create interview session");
      }
    } catch (error) {
      console.error("Start interview error:", error);
      alert(error.response?.data?.detail || error.response?.data?.message || "Failed to initialize interview. Check your coin balance.");
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="bg-[#F8F9FB] min-h-screen text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-700">
      {/* ── Top Navigation Bar ── */}
      <header className="h-16 px-4 sm:px-8 max-w-7xl mx-auto flex items-center justify-between">
        <button
          onClick={() => navigate("/dashboard")}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200/80 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs cursor-pointer"
        >
          <FiArrowLeft size={14} />
          <span>Back</span>
        </button>

        <div
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <GiArtificialHive size={18} />
          </div>
          <span className="font-extrabold text-base tracking-tight text-slate-900">
            Fresher.Ai
          </span>
        </div>
      </header>

      {/* ── Main Container ── */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-4 pb-16 space-y-6">
        {/* ── Hero Banner Section ── */}
        <div className="relative rounded-3xl bg-transparent py-2 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex-1 text-left">
            <p className="text-[11px] font-bold tracking-widest text-indigo-600 uppercase mb-2">
              AI Interview Practice
            </p>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Configure your{" "}
              <span className="text-[#4F46E5] bg-gradient-to-r from-[#4F46E5] to-[#7C3AED] bg-clip-text text-transparent">
                interview
              </span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-2 max-w-xl">
              Tell us what you're preparing for, and we'll create an interview tailored to you.
            </p>
          </div>

          {/* Right Mascot Illustration */}
          <div className="relative w-40 sm:w-48 aspect-video flex items-center justify-center shrink-0">
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-300/30 to-purple-400/30 blur-xl transform scale-90" />
            
            {/* Floating Chat Bubble */}
            <motion.div
              animate={{ y: [4, -4, 4] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-1 right-2 z-20 w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-md text-xs"
            >
              <FiMessageSquare size={14} />
            </motion.div>

            {/* AI Bot Mascot SVG */}
            <div className="relative z-10 w-28 h-28 flex items-center justify-center">
              <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-lg" fill="none">
                <ellipse cx="100" cy="165" rx="42" ry="18" fill="#CBD5E1" opacity="0.5" />
                <rect x="65" y="110" width="70" height="50" rx="20" fill="url(#setup_body)" />
                <rect x="75" y="122" width="50" height="24" rx="10" fill="#0F172A" />
                <circle cx="90" cy="134" r="3" fill="#60A5FA" />
                <circle cx="100" cy="134" r="3" fill="#34D399" />
                <circle cx="110" cy="134" r="3" fill="#F472B6" />
                <rect x="90" y="98" width="20" height="15" rx="4" fill="#94A3B8" />
                <rect x="52" y="45" width="96" height="60" rx="24" fill="url(#setup_head)" stroke="#FFFFFF" strokeWidth="3" />
                <circle cx="48" cy="75" r="9" fill="#818CF8" />
                <circle cx="152" cy="75" r="9" fill="#818CF8" />
                <rect x="62" y="55" width="76" height="40" rx="16" fill="#0F172A" />
                <circle cx="83" cy="74" r="7" fill="#60A5FA" />
                <circle cx="85" cy="72" r="2.5" fill="#FFFFFF" />
                <circle cx="117" cy="74" r="7" fill="#60A5FA" />
                <circle cx="119" cy="72" r="2.5" fill="#FFFFFF" />
                <path d="M93 83C96 86 104 86 107 83" stroke="#60A5FA" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="100" y1="45" x2="100" y2="30" stroke="#818CF8" strokeWidth="3" strokeLinecap="round" />
                <circle cx="100" cy="27" r="5" fill="#A78BFA" />
                <defs>
                  <linearGradient id="setup_head" x1="52" y1="45" x2="148" y2="105" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#F8FAFC" />
                    <stop offset="1" stopColor="#E2E8F0" />
                  </linearGradient>
                  <linearGradient id="setup_body" x1="65" y1="110" x2="135" y2="160" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#FFFFFF" />
                    <stop offset="1" stopColor="#E2E8F0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>

        {/* ── 3-Step Horizontal Stepper ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-2 border-y border-slate-200/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#4F46E5] text-white flex items-center justify-center text-xs font-bold shadow-xs shrink-0">
              01
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900">Setup</p>
              <p className="text-[11px] text-slate-400">Tell us about your preferences</p>
            </div>
          </div>

          <div className="flex items-center gap-3 opacity-60">
            <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0">
              02
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-700">Interview</p>
              <p className="text-[11px] text-slate-400">Answer AI generated questions</p>
            </div>
          </div>

          <div className="flex items-center gap-3 opacity-60">
            <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0">
              03
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-700">Feedback</p>
              <p className="text-[11px] text-slate-400">Get insights &amp; improve</p>
            </div>
          </div>
        </div>

        {/* ── 2-Column Main Content ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[38%_62%] gap-6 items-start">
          {/* ── Left Feature Highlights Card ── */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs space-y-5">
            {/* Highlight 1 */}
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <BsStars size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Your AI interview, built for you
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  Practice realistic interview questions and receive personalised feedback to improve before your next opportunity.
                </p>
              </div>
            </div>

            <div className="h-px bg-slate-100" />

            {/* Highlight 2 */}
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                <HiSparkles size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Personalized AI Questions
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  Questions tailored to your selected role and interview type.
                </p>
              </div>
            </div>

            {/* Highlight 3 */}
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <FiFileText size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Resume-Based Interview
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  Use your experience and skills to generate more relevant questions.
                </p>
              </div>
            </div>

            {/* Highlight 4 */}
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <FiBarChart2 size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Detailed Performance Report
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  Understand your strengths and discover where you can improve.
                </p>
              </div>
            </div>

            {/* Highlight 5 */}
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center shrink-0">
                <FiMessageSquare size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Real Interview Experience
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                  Practice in a focused environment designed to feel like a real interview.
                </p>
              </div>
            </div>

            {/* Preparation Tip Box */}
            <div className="rounded-2xl bg-indigo-50/70 border border-indigo-100 p-4 flex items-start gap-3 mt-4">
              <div className="w-7 h-7 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 text-xs">
                <BsLightbulb size={14} />
              </div>
              <div>
                <h4 className="text-xs font-bold text-indigo-900">Preparation tip</h4>
                <p className="text-[11px] text-indigo-700/80 mt-0.5 leading-relaxed">
                  Choose the interview type closest to the role you're currently preparing for.
                </p>
              </div>
            </div>
          </div>

          {/* ── Right Interactive Setup Form Card ── */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs space-y-6">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">
                Interview details
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Set your preferences and let AI personalise your practice.
              </p>
            </div>

            {/* 1. Target Role Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">
                What role are you preparing for?
              </label>
              <div className="relative">
                <FiBriefcase className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="Backend Developer, React Engineer, Product Manager..."
                  className="w-full h-12 rounded-2xl bg-slate-50/80 border border-slate-200/80 pl-11 pr-4 text-xs sm:text-sm font-medium text-slate-800 outline-none focus:border-indigo-500 focus:bg-white transition"
                />
              </div>
            </div>

            {/* 2. Choose Interview Type */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700">
                Choose your interview type
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* Technical Card */}
                <div
                  onClick={() => setType("technical")}
                  className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between relative ${
                    type === "technical"
                      ? "border-indigo-600 bg-indigo-50/30 shadow-xs"
                      : "border-slate-200/80 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-mono font-bold text-xs shadow-xs">
                      &lt;/&gt;
                    </div>
                    {type === "technical" && (
                      <div className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center">
                        <FiCheck size={12} />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">
                      Technical Interview
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                      Coding, DSA, CS fundamentals and technical concepts.
                    </p>
                  </div>
                </div>

                {/* HR Card */}
                <div
                  onClick={() => setType("hr")}
                  className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between relative ${
                    type === "hr"
                      ? "border-orange-500 bg-orange-50/30 shadow-xs"
                      : "border-slate-200/80 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-xs">
                      <FiMessageSquare size={16} />
                    </div>
                    {type === "hr" && (
                      <div className="w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
                        <FiCheck size={12} />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">
                      HR Interview
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                      Behavioural, communication and workplace questions.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. Resume Personalization Card & Toggle */}
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0">
                    <FiFileText size={16} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">
                      Personalise with your resume
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Use your experience and skills to generate more relevant interview questions.
                    </p>
                  </div>
                </div>

                {/* Custom Toggle Switch */}
                <button
                  type="button"
                  onClick={() => setUseResume(!useResume)}
                  className={`relative shrink-0 w-12 h-6.5 rounded-full transition-colors ${
                    useResume ? "bg-[#4F46E5]" : "bg-slate-300"
                  }`}
                >
                  <div
                    className={`absolute top-1 w-4.5 h-4.5 rounded-full bg-white transition-all shadow-xs ${
                      useResume ? "left-6.5" : "left-1"
                    }`}
                  />
                </button>
              </div>

              {/* Resume Upload / Active Banner if Enabled */}
              {useResume && (
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between gap-2 text-xs">
                  {resume ? (
                    <div className="flex items-center gap-2 text-emerald-600 font-semibold">
                      <FiCheckCircle size={14} />
                      <span>Resume ready ({resume.name || "Loaded"})</span>
                    </div>
                  ) : (
                    <div className="text-amber-600 font-medium">
                      No resume uploaded yet.
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => setShowUploadModal(true)}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-700 underline cursor-pointer"
                  >
                    {resume ? "Change Resume" : "Upload Resume (+10 coins)"}
                  </button>
                </div>
              )}
            </div>

            {/* 4. Ready to Start Summary Pill */}
            <div className="rounded-xl bg-slate-100/70 border border-slate-200/60 px-4 py-2.5 flex flex-wrap items-center gap-3 text-xs text-slate-600">
              <span className="font-bold text-slate-700">Ready to start:</span>
              <span className="inline-flex items-center gap-1 bg-white px-2 py-1 rounded-lg border border-slate-200/60 font-medium">
                💼 {role || "Custom Role"}
              </span>
              <span className="inline-flex items-center gap-1 bg-white px-2 py-1 rounded-lg border border-slate-200/60 font-medium">
                {type === "technical" ? "</> Technical Interview" : "🗣️ HR Interview"}
              </span>
              <span className="inline-flex items-center gap-1 bg-white px-2 py-1 rounded-lg border border-slate-200/60 font-medium">
                📄 Resume personalisation: {useResume ? "On" : "Off"}
              </span>
            </div>

            {/* 5. Start Button */}
            <div>
              <button
                type="button"
                disabled={!role.trim() || starting}
                onClick={start}
                className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
              >
                {starting ? (
                  <span>Generating Interview Session...</span>
                ) : (
                  <>
                    <BsStars size={16} />
                    <span>Start AI Interview</span>
                    <FiArrowRight size={15} />
                  </>
                )}
              </button>
              <p className="text-center text-[11px] text-slate-400 mt-2.5">
                Your interview will be generated based on your selected preferences. (50 Coins)
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* ── Optional Resume Upload Modal ── */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Upload Your Resume</h3>
            <p className="text-xs text-slate-500">
              Upload a PDF resume to generate tailored interview questions and ATS analytics.
            </p>

            <label className="border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition">
              <FiUploadCloud size={32} className="text-indigo-600 mb-2" />
              <span className="text-xs font-semibold text-slate-700">Choose PDF file</span>
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files[0]) setFile(e.target.files[0]);
                }}
              />
            </label>

            {file && (
              <p className="text-xs text-slate-600 truncate font-mono bg-slate-50 p-2 rounded-lg">
                📄 {file.name}
              </p>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!file || uploading}
                onClick={uploadResume}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm transition disabled:opacity-50"
              >
                {uploading ? "Uploading..." : "Upload (+10 coins)"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Step1SetUp;