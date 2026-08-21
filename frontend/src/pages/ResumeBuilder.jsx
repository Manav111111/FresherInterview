import { useState } from "react";
import {
  FiArrowLeft,
  FiArrowRight,
  FiEye,
  FiZap,
  FiUser,
  FiBookOpen,
  FiBriefcase,
  FiCode,
  FiFolder,
  FiFileText,
  FiCheck,
  FiChevronDown
} from "react-icons/fi";
import { BsStars, BsCheckCircleFill } from "react-icons/bs";
import { GiArtificialHive } from "react-icons/gi";
import { motion, AnimatePresence } from "motion/react";
import ResumePreview from "../components/resume/ResumePreview";
import ResumeForm from "../components/resume/ResumeForm";
import initialData from "../components/resume/initialData";
import AIResumeReviewModal from "../components/resume/AIResumeReviewModal";
import { analyzeResumeData } from "../api/resume.api";
import { useNavigate } from "react-router-dom";

// Steps aligned with user reference design
const STEPS = [
  {
    step: 1,
    title: "Personal",
    highlight: "Information",
    fullTitle: "Personal Info",
    subtitle: "Let's start with your basic details. This information will appear at the top of your resume.",
    icon: FiUser,
    illustration: "id_card",
  },
  {
    step: 2,
    title: "Academic",
    highlight: "Education",
    fullTitle: "Education",
    subtitle: "Add your college, degree, CGPA and graduation year to showcase your educational background.",
    icon: FiBookOpen,
    illustration: "education",
  },
  {
    step: 3,
    title: "Work",
    highlight: "Experience",
    fullTitle: "Experience",
    subtitle: "Highlight your internships, full-time jobs, and impactful contributions with key metrics.",
    icon: FiBriefcase,
    illustration: "experience",
  },
  {
    step: 4,
    title: "Technical",
    highlight: "Skills",
    fullTitle: "Skills",
    subtitle: "List your programming languages, frameworks, developer tools, and databases.",
    icon: FiCode,
    illustration: "skills",
  },
  {
    step: 5,
    title: "Featured",
    highlight: "Projects",
    fullTitle: "Projects",
    subtitle: "Add live project links, tech stack details, and key features to prove hands-on mastery.",
    icon: FiFolder,
    illustration: "projects",
  },
  {
    step: 6,
    title: "Professional",
    highlight: "Summary",
    fullTitle: "Summary",
    subtitle: "Write a compelling 2-3 sentence overview highlighting your engineering strengths.",
    icon: FiFileText,
    illustration: "summary",
  },
];

const TOTAL_STEPS = STEPS.length;

export default function ResumeBuilder({ user, setUser }) {
  const [data, setData] = useState(initialData);
  const [currentStep, setCurrentStep] = useState(1);
  const [showPreview, setShowPreview] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);

  const navigate = useNavigate();

  const getInitials = (name) => {
    if (!name) return "FC";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const handleAIReview = async () => {
    setReviewModalOpen(true);
    setReviewLoading(true);
    try {
      const res = await analyzeResumeData(data);
      if (res?.data) {
        setAnalysis(res.data);
      }
    } catch (err) {
      console.error("AI Review failed:", err);
      alert("Failed to analyze resume with AI. Please try again.");
    } finally {
      setReviewLoading(false);
    }
  };

  const goNext = () => {
    if (currentStep < TOTAL_STEPS) setCurrentStep(currentStep + 1);
  };

  const goPrev = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const isLastStep = currentStep === TOTAL_STEPS;
  const activeStep = STEPS.find((s) => s.step === currentStep);

  // Calculate dynamic completion percentage
  const calculateCompletion = () => {
    let filled = 0;
    let total = 6;
    if (data.name?.trim()) filled++;
    if (data.education?.length > 0 && data.education[0].college) filled++;
    if (data.experience?.length > 0 && data.experience[0].company) filled++;
    if (data.skills?.trim()) filled++;
    if (data.projects?.length > 0 && data.projects[0].name) filled++;
    if (data.summary?.trim()) filled++;
    return Math.round((filled / total) * 100);
  };

  const completionPct = calculateCompletion();

  // ── Show Preview Page ──────────────────────────────────────────────────────
  if (showPreview) {
    return <ResumePreview data={data} user={user} setUser={setUser} onBack={() => setShowPreview(false)} />;
  }

  // ── Step Illustration Component ──
  const renderIllustration = (type) => {
    switch (type) {
      case "id_card":
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute -top-1 left-2 text-indigo-400 text-sm">✦</div>
            <div className="absolute top-2 right-4 text-amber-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <rect x="25" y="20" width="150" height="95" rx="16" fill="url(#id_card_grad)" stroke="#E0E7FF" strokeWidth="2" />
              <circle cx="65" cy="58" r="16" fill="#C7D2FE" />
              <path d="M52 88C52 78 78 78 78 88" stroke="#818CF8" strokeWidth="4" strokeLinecap="round" />
              <rect x="95" y="44" width="60" height="8" rx="4" fill="#818CF8" />
              <rect x="95" y="60" width="45" height="6" rx="3" fill="#C7D2FE" />
              <rect x="95" y="74" width="52" height="6" rx="3" fill="#E0E7FF" />
              <defs>
                <linearGradient id="id_card_grad" x1="25" y1="20" x2="175" y2="115" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#EEF2FF" />
                  <stop offset="1" stopColor="#E0E7FF" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        );
      case "education":
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute top-1 left-3 text-purple-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <ellipse cx="100" cy="115" rx="45" ry="12" fill="#E2E8F0" opacity="0.6" />
              <path d="M100 30L160 55L100 80L40 55L100 30Z" fill="#4F46E5" />
              <path d="M100 80L160 55V75L100 100L40 75V55L100 80Z" fill="#3730A3" />
              <path d="M65 72V98C65 108 135 108 135 98V72" fill="#6366F1" opacity="0.9" />
              <circle cx="160" cy="55" r="4" fill="#F59E0B" />
              <line x1="160" y1="55" x2="168" y2="85" stroke="#F59E0B" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </div>
        );
      case "experience":
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute top-2 right-4 text-orange-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <ellipse cx="100" cy="115" rx="50" ry="12" fill="#E2E8F0" opacity="0.6" />
              <rect x="45" y="45" width="110" height="70" rx="14" fill="#F97316" />
              <rect x="55" y="40" width="90" height="75" rx="12" fill="#FB923C" />
              <path d="M78 40V30C78 25 122 25 122 30V40" stroke="#EA580C" strokeWidth="4" strokeLinecap="round" fill="none" />
              <line x1="45" y1="75" x2="155" y2="75" stroke="#EA580C" strokeWidth="3" />
              <rect x="92" y="70" width="16" height="12" rx="3" fill="#FED7AA" />
            </svg>
          </div>
        );
      case "skills":
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute top-1 left-2 text-emerald-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <rect x="40" y="30" width="120" height="80" rx="16" fill="#10B981" />
              <rect x="48" y="38" width="104" height="64" rx="10" fill="#064E3B" />
              <text x="65" y="78" fill="#34D399" fontFamily="monospace" fontSize="22" fontWeight="bold">&lt;/&gt;</text>
              <circle cx="125" cy="70" r="5" fill="#34D399" />
              <circle cx="138" cy="70" r="5" fill="#6EE7B7" />
            </svg>
          </div>
        );
      case "projects":
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute top-1 right-3 text-pink-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <rect x="40" y="35" width="120" height="75" rx="14" fill="#EC4899" />
              <path d="M40 50L100 85L160 50" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
              <circle cx="100" cy="75" r="14" fill="#FDF2F8" />
              <path d="M95 75L98 78L106 70" stroke="#DB2777" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        );
      case "summary":
      default:
        return (
          <div className="relative w-44 h-32 mx-auto flex items-center justify-center">
            <div className="absolute top-1 left-3 text-indigo-400 text-sm">✦</div>
            <svg viewBox="0 0 200 140" className="w-full h-full drop-shadow-md" fill="none">
              <rect x="55" y="20" width="90" height="100" rx="12" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="2" />
              <rect x="70" y="38" width="60" height="8" rx="4" fill="#4F46E5" />
              <rect x="70" y="54" width="50" height="5" rx="2.5" fill="#CBD5E1" />
              <rect x="70" y="65" width="55" height="5" rx="2.5" fill="#CBD5E1" />
              <rect x="70" y="76" width="45" height="5" rx="2.5" fill="#CBD5E1" />
              <rect x="70" y="87" width="50" height="5" rx="2.5" fill="#CBD5E1" />
              <circle cx="135" cy="98" r="10" fill="#F59E0B" />
              <text x="131" y="102" fill="#FFFFFF" fontSize="12" fontWeight="bold">★</text>
            </svg>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FB] text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-700 flex flex-col pb-16">
      <AIResumeReviewModal
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        loading={reviewLoading}
        analysis={analysis}
      />

      {/* ── Top Navbar ── */}
      <nav className="h-16 border-b border-slate-200/70 bg-white/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto h-full flex items-center justify-between">
          {/* Left Brand */}
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
            <span className="ml-2 rounded-full bg-purple-50 border border-purple-100/80 px-2.5 py-0.5 text-[11px] font-bold text-purple-700">
              Resume Builder
            </span>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleAIReview}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-purple-50 border border-purple-200/80 text-xs font-bold text-purple-700 hover:bg-purple-100 transition shadow-2xs cursor-pointer"
            >
              <FiZap size={13} className="text-purple-600" />
              <span className="hidden sm:inline">AI ATS Review</span>
            </button>

            <button
              onClick={() => setShowPreview(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white border border-slate-200/80 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs cursor-pointer"
            >
              <FiEye size={13} className="text-slate-500" />
              <span className="hidden sm:inline">Preview</span>
            </button>

            {/* User Avatar Circle */}
            <div className="relative">
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-1.5 p-1 rounded-full hover:bg-slate-100 transition cursor-pointer"
              >
                <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shadow-xs">
                  {getInitials(user?.name)}
                </div>
                <FiChevronDown size={14} className="text-slate-500" />
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-2xl p-2 shadow-xl z-50">
                  <div className="px-3 py-2 border-b border-slate-100">
                    <p className="text-xs font-bold text-slate-900 truncate">{user?.name || "Candidate"}</p>
                    <p className="text-[10px] text-slate-500 truncate">{user?.email || "candidate@fresherai.com"}</p>
                  </div>
                  <button
                    onClick={() => navigate("/dashboard")}
                    className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 rounded-lg transition"
                  >
                    Dashboard
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* ── Main Content Container ── */}
      <div className="max-w-6xl mx-auto w-full px-4 sm:px-6 pt-6 space-y-6">
        {/* ── 6-Step Horizontal Stepper ── */}
        <div className="flex items-center justify-between max-w-3xl mx-auto px-4 py-2">
          {STEPS.map((s, index) => {
            const isActive = s.step === currentStep;
            const isCompleted = s.step < currentStep;

            return (
              <div key={s.step} className="flex items-center flex-1 last:flex-none">
                {/* Step Node */}
                <div
                  onClick={() => setCurrentStep(s.step)}
                  className="flex flex-col items-center gap-1.5 cursor-pointer group"
                >
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-xs ${
                      isActive
                        ? "bg-[#4F46E5] text-white ring-4 ring-indigo-100 scale-105"
                        : isCompleted
                        ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
                        : "bg-slate-100 text-slate-500 border border-slate-200"
                    }`}
                  >
                    {isCompleted ? <FiCheck size={14} /> : s.step}
                  </div>
                  <span
                    className={`text-[11px] font-semibold transition-colors hidden sm:block ${
                      isActive ? "text-slate-900 font-bold" : "text-slate-500"
                    }`}
                  >
                    {s.fullTitle}
                  </span>
                </div>

                {/* Connector Line */}
                {index < STEPS.length - 1 && (
                  <div className="flex-1 h-0.5 mx-2 sm:mx-3 bg-slate-200">
                    <div
                      className="h-full bg-indigo-600 transition-all duration-300"
                      style={{
                        width: isCompleted ? "100%" : isActive ? "50%" : "0%",
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Main Card Container ── */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-xs">
          <div className="grid grid-cols-1 lg:grid-cols-[35%_65%] gap-8 items-start">
            {/* ── Left Step Intro & 3D Illustration Card ── */}
            <div className="bg-indigo-50/40 border border-indigo-100/60 rounded-3xl p-6 flex flex-col justify-between h-full min-h-[380px]">
              <div>
                <div className="w-11 h-11 rounded-2xl bg-white border border-indigo-100 text-indigo-600 flex items-center justify-center shadow-xs text-lg mb-4">
                  {activeStep && <activeStep.icon size={20} />}
                </div>
                <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight leading-snug">
                  {activeStep.title}{" "}
                  <span className="text-[#4F46E5] bg-gradient-to-r from-[#4F46E5] to-[#7C3AED] bg-clip-text text-transparent">
                    {activeStep.highlight}
                  </span>
                </h2>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                  {activeStep.subtitle}
                </p>
              </div>

              {/* 3D Illustration */}
              <div className="pt-6">
                {renderIllustration(activeStep.illustration)}
              </div>
            </div>

            {/* ── Right Form Fields Column ── */}
            <div className="flex flex-col justify-between space-y-6">
              {/* Header Badge */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-700">
                  Step {currentStep} of {TOTAL_STEPS}
                </span>
                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold px-2.5 py-0.5 rounded-full">
                  <BsCheckCircleFill size={10} className="text-emerald-500" />
                  <span>{completionPct}% complete</span>
                </span>
              </div>

              {/* Step Form */}
              <div className="min-h-[280px]">
                <ResumeForm step={currentStep} data={data} setData={setData} />
              </div>

              {/* ── Bottom Navigation Bar ── */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                {/* Previous Button */}
                <button
                  onClick={goPrev}
                  disabled={currentStep === 1}
                  className={`h-11 px-5 rounded-2xl border text-xs font-bold flex items-center gap-1.5 transition ${
                    currentStep === 1
                      ? "border-slate-200 text-slate-300 cursor-not-allowed bg-slate-50/50"
                      : "border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer shadow-2xs"
                  }`}
                >
                  <FiArrowLeft size={14} />
                  <span>Previous</span>
                </button>

                {/* Dot Pagination Indicator */}
                <div className="flex items-center gap-1.5">
                  {STEPS.map((s) => (
                    <button
                      key={s.step}
                      onClick={() => setCurrentStep(s.step)}
                      className={`rounded-full transition-all cursor-pointer ${
                        s.step === currentStep
                          ? "w-6 h-2 bg-[#4F46E5]"
                          : s.step < currentStep
                          ? "w-2 h-2 bg-indigo-300"
                          : "w-2 h-2 bg-slate-200 hover:bg-slate-300"
                      }`}
                    />
                  ))}
                </div>

                {/* Next / Preview Button */}
                {isLastStep ? (
                  <button
                    onClick={() => setShowPreview(true)}
                    className="h-11 px-6 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs sm:text-sm font-bold shadow-md shadow-indigo-500/25 flex items-center gap-1.5 transition hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
                  >
                    <FiEye size={15} />
                    <span>Preview Resume</span>
                  </button>
                ) : (
                  <button
                    onClick={goNext}
                    className="h-11 px-7 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs sm:text-sm font-bold shadow-md shadow-indigo-500/25 flex items-center gap-1.5 transition hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
                  >
                    <span>Next</span>
                    <FiArrowRight size={15} />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}