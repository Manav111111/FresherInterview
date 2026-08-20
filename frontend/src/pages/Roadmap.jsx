import { useState, useEffect } from "react";
import { useSelector } from "react-redux";
import { motion, AnimatePresence } from "motion/react";
import {
  FiSend, FiFileText, FiClock,
  FiZap, FiX, FiCheck, FiChevronDown,
  FiArrowRight, FiBriefcase, FiDatabase,
  FiCode, FiCpu, FiLayers, FiCheckCircle
} from "react-icons/fi";
import { BsStars, BsRocketTakeoff, BsLightbulb } from "react-icons/bs";
import { GiArtificialHive, GiBrain } from "react-icons/gi";
import { useNavigate } from "react-router-dom";
import RoadmapResult from "../components/roadmap/RoadmapResult";
import { generateRoadmap, getAllRoadmaps, getRoadmapById as apiGetRoadmapById } from "../api/roadmap.api";
import { useCoins } from "../api/user.api";

const PACKAGE_OPTIONS = ["10 LPA", "15 LPA", "20 LPA", "30 LPA", "40 LPA", "50+ LPA"];

const POPULAR_ROLES = [
  {
    title: "Frontend Developer",
    desc: "Learn modern frontend technologies and frameworks.",
    icon: FiCode,
    color: "from-indigo-500 to-purple-600",
    bg: "bg-indigo-50 text-indigo-600",
    defaultPackage: "15 LPA",
  },
  {
    title: "Backend Engineer",
    desc: "Master backend development, databases and APIs.",
    icon: FiDatabase,
    color: "from-orange-500 to-amber-500",
    bg: "bg-orange-50 text-orange-600",
    defaultPackage: "20 LPA",
  },
  {
    title: "ML Engineer",
    desc: "Dive into machine learning, AI models and data science.",
    icon: GiBrain,
    color: "from-emerald-500 to-teal-600",
    bg: "bg-emerald-50 text-emerald-600",
    defaultPackage: "30 LPA",
  },
];

// ─── Navbar ───────────────────────────────────────────────────────────────────
function Navbar({ user, onHistoryClick }) {
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  const getInitials = (name) => {
    if (!name) return "FC";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  return (
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
          <span className="ml-2 rounded-full bg-indigo-50 border border-indigo-100/80 px-2.5 py-0.5 text-[11px] font-bold text-indigo-600">
            Roadmap Generator
          </span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onHistoryClick}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white border border-slate-200/80 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs cursor-pointer"
          >
            <FiClock size={13} className="text-slate-500" />
            <span>History</span>
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
  );
}

// ─── Main Roadmap Page ────────────────────────────────────────────────────────
export default function Roadmap({ user, setUser }) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [roadmap, setRoadmap]         = useState(null);
  const [role, setRole]               = useState("Backend Developer");
  const [targetPackage, setTargetPackage] = useState(PACKAGE_OPTIONS[2]); // default "20 LPA"
  const [packageOpen, setPackageOpen] = useState(false);
  const [useResume, setUseResume]     = useState(false);
  const [loading, setLoading]         = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [history, setHistory]         = useState([]);
  const [error, setError]             = useState("");

  const { resume } = useSelector((state) => state.resume);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRoadmaps();
  }, []);

  const fetchRoadmaps = async () => {
    try {
      setHistoryLoading(true);
      const response = await getAllRoadmaps();
      setHistory(response?.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSelectRoadmap = async (id) => {
    try {
      const response = await apiGetRoadmapById(id);
      if (response?.data) {
        setRoadmap(response.data);
        setHistoryOpen(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // ── Generate a new roadmap ──
  async function handleGenerate(customRole) {
    const selectedRole = (customRole || role).trim();
    if (!selectedRole || loading) return;
    setLoading(true);
    setError("");
    try {
      const coinResponse = await useCoins({ coins: 20, action: "roadmap" });
      if (coinResponse?.interviewCoin !== undefined) {
        setUser((prev) => ({ ...prev, interviewCoin: coinResponse.interviewCoin }));
      }
      const response = await generateRoadmap({
        role: selectedRole,
        targetPackage,
        useResume,
        resume: useResume ? resume : null,
      });
      if (response?.data) {
        setRoadmap(response.data);
        fetchRoadmaps();
      }
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail || err?.message || "Failed to generate roadmap. Please check your coin balance.");
    } finally {
      setLoading(false);
    }
  }

  const handleQuickSelect = (item) => {
    setRole(item.title);
    setTargetPackage(item.defaultPackage);
  };

  return (
    <div className="bg-[#F8F9FB] min-h-screen text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-700 pb-20">
      {/* Navbar */}
      <Navbar user={user} onHistoryClick={() => setHistoryOpen(true)} />

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        {/* If a roadmap is already generated or viewed */}
        {roadmap ? (
          <RoadmapResult
            roadmap={roadmap}
            onClear={() => setRoadmap(null)}
          />
        ) : (
          <div className="space-y-8">
            {/* ── Hero Centerpiece with 3D Rocket Illustration ── */}
            <div className="text-center pt-4 pb-2 relative">
              {/* Rocket vector art */}
              <div className="relative w-36 h-32 mx-auto flex items-center justify-center">
                <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-pink-200/40 via-purple-200/40 to-indigo-200/40 blur-xl scale-125" />
                
                {/* Floating Stars */}
                <motion.div
                  animate={{ y: [-4, 4, -4], rotate: [0, 15, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute top-2 left-2 text-indigo-400 text-sm"
                >
                  ✦
                </motion.div>
                <motion.div
                  animate={{ y: [4, -4, 4], rotate: [0, -15, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute top-4 right-3 text-amber-400 text-sm"
                >
                  ✦
                </motion.div>

                {/* Rocket SVG */}
                <svg viewBox="0 0 200 200" className="w-28 h-28 drop-shadow-xl" fill="none">
                  {/* Clouds */}
                  <ellipse cx="100" cy="165" rx="55" ry="20" fill="#E2E8F0" opacity="0.6" />
                  <ellipse cx="75" cy="155" rx="25" ry="15" fill="#EEF2FF" />
                  <ellipse cx="125" cy="155" rx="25" ry="15" fill="#EEF2FF" />
                  <ellipse cx="100" cy="150" rx="35" ry="18" fill="#FFFFFF" />

                  {/* Flame */}
                  <path d="M92 135 C92 165, 108 165, 108 135 Z" fill="#F97316" />
                  <path d="M96 135 C96 155, 104 155, 104 135 Z" fill="#FDE047" />

                  {/* Rocket Body */}
                  <path d="M100 30 C125 70, 125 125, 100 135 C75 125, 75 70, 100 30 Z" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="2" />
                  <path d="M100 30 C110 50, 110 65, 100 70 C90 65, 90 50, 100 30 Z" fill="#EC4899" />
                  
                  {/* Wings */}
                  <path d="M78 105 L60 130 C70 135, 80 130, 82 125 Z" fill="#EC4899" />
                  <path d="M122 105 L140 130 C130 135, 120 130, 118 125 Z" fill="#EC4899" />

                  {/* Window */}
                  <circle cx="100" cy="85" r="12" fill="#0284C7" stroke="#FFFFFF" strokeWidth="2.5" />
                  <circle cx="100" cy="85" r="8" fill="#38BDF8" />
                  <circle cx="98" cy="83" r="2.5" fill="#FFFFFF" />
                </svg>
              </div>

              {/* Title & Description */}
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
                <span className="text-[#4F46E5]">AI</span> Roadmap Generator
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-2 max-w-md mx-auto leading-relaxed">
                Generate a personalised roadmap for your dream job. Choose a role and let AI build a complete learning path.
              </p>
            </div>

            {/* ── 3 Quick-Select Role Cards ── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {POPULAR_ROLES.map((item) => {
                const Icon = item.icon;
                const isSelected = role === item.title;
                return (
                  <motion.div
                    key={item.title}
                    whileHover={{ y: -3, scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => handleQuickSelect(item)}
                    className={`bg-white rounded-3xl border-2 p-6 shadow-xs transition-all cursor-pointer flex flex-col justify-between relative ${
                      isSelected
                        ? "border-indigo-600 shadow-md shadow-indigo-500/10"
                        : "border-slate-200/80 hover:border-slate-300"
                    }`}
                  >
                    <div>
                      {/* Icon */}
                      <div className={`w-12 h-12 rounded-2xl ${item.bg} flex items-center justify-center mb-4 text-xl shadow-2xs`}>
                        <Icon />
                      </div>

                      {/* Content */}
                      <h3 className="text-sm font-bold text-slate-900">
                        {item.title}
                      </h3>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                        {item.desc}
                      </p>
                    </div>

                    {/* Arrow Button at bottom right */}
                    <div className="mt-5 flex items-center justify-end">
                      <div className={`w-8 h-8 rounded-full border flex items-center justify-center transition-colors ${
                        isSelected
                          ? "bg-indigo-600 border-indigo-600 text-white"
                          : "border-slate-200 text-slate-400 group-hover:border-slate-300"
                      }`}>
                        <FiArrowRight size={14} />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* ── Bottom Custom Input & Action Bar ── */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-xs space-y-3">
              <p className="text-xs font-semibold text-slate-500 ml-1">
                Or enter your own role
              </p>

              <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
                {/* 1. Custom Role Text Input */}
                <div className="flex-1 relative">
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <FiBriefcase size={15} />
                  </div>
                  <input
                    type="text"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="Enter target role (e.g. DevOps Engineer, Data Analyst...)"
                    className="w-full h-12 rounded-2xl bg-slate-50/80 border border-slate-200/80 pl-13 pr-4 text-xs sm:text-sm font-medium text-slate-800 outline-none focus:border-indigo-500 focus:bg-white transition"
                  />
                </div>

                {/* 2. Package Selector Dropdown */}
                <div className="relative shrink-0">
                  <button
                    type="button"
                    onClick={() => setPackageOpen(!packageOpen)}
                    className="h-12 px-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 text-xs font-semibold text-slate-700 flex items-center gap-2 hover:bg-slate-100 transition cursor-pointer"
                  >
                    <span>{targetPackage}</span>
                    <FiChevronDown size={14} className="text-slate-400" />
                  </button>

                  {packageOpen && (
                    <div className="absolute right-0 mt-2 w-36 bg-white border border-slate-200 rounded-2xl p-1.5 shadow-xl z-50">
                      {PACKAGE_OPTIONS.map((pkg) => (
                        <button
                          key={pkg}
                          type="button"
                          onClick={() => {
                            setTargetPackage(pkg);
                            setPackageOpen(false);
                          }}
                          className={`w-full text-left px-3 py-2 text-xs font-medium rounded-xl transition ${
                            targetPackage === pkg
                              ? "bg-indigo-50 text-indigo-600 font-bold"
                              : "text-slate-700 hover:bg-slate-50"
                          }`}
                        >
                          {pkg}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* 3. Resume Toggle Button */}
                <button
                  type="button"
                  onClick={() => setUseResume(!useResume)}
                  className={`h-12 px-4 rounded-2xl border text-xs font-semibold flex items-center gap-2 transition cursor-pointer shrink-0 ${
                    useResume
                      ? "bg-indigo-50 border-indigo-300 text-indigo-600 font-bold"
                      : "bg-slate-50/80 border-slate-200/80 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <FiFileText size={15} />
                  <span>Resume</span>
                  {useResume && <FiCheck size={13} className="text-indigo-600" />}
                </button>

                {/* 4. Generate Button */}
                <button
                  type="button"
                  disabled={!role.trim() || loading}
                  onClick={() => handleGenerate()}
                  className="h-12 px-6 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs sm:text-sm font-bold shadow-md shadow-indigo-500/25 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer shrink-0"
                >
                  {loading ? (
                    <span>Generating...</span>
                  ) : (
                    <>
                      <BsStars size={15} />
                      <span>Generate Roadmap</span>
                    </>
                  )}
                </button>
              </div>

              {error && (
                <p className="text-xs text-rose-500 mt-2 font-medium">
                  ⚠️ {error}
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Slide-over History Drawer ── */}
      <AnimatePresence>
        {historyOpen && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setHistoryOpen(false)}
              className="absolute inset-0 bg-slate-900/30 backdrop-blur-xs"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative z-10 w-full max-w-md bg-white border-l border-slate-200 h-full p-6 flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <FiClock size={16} className="text-indigo-600" />
                  <h3 className="font-bold text-slate-900 text-base">Roadmap History</h3>
                </div>
                <button
                  onClick={() => setHistoryOpen(false)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition cursor-pointer"
                >
                  <FiX size={18} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto py-4 space-y-3">
                {historyLoading ? (
                  <p className="text-xs text-slate-400 text-center py-8">Loading saved roadmaps...</p>
                ) : history.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 space-y-2">
                    <p className="text-xs">No past roadmaps found.</p>
                    <p className="text-[11px] text-slate-400">Generate your first roadmap to save it here!</p>
                  </div>
                ) : (
                  history.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleSelectRoadmap(item.id)}
                      className="p-4 rounded-2xl border border-slate-200/80 hover:border-indigo-400 hover:bg-indigo-50/20 transition cursor-pointer space-y-1 group"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-900 group-hover:text-indigo-600 transition">
                          {item.title || item.role}
                        </h4>
                        <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                          {item.package || item.target_package}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        {item.level || "Standard Path"} • {item.duration || "Self-paced"}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}