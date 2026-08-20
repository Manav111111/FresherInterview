import { useState } from "react";
import { motion } from "motion/react";
import {
  FiFileText,
  FiStar,
  FiMap,
  FiVideo,
  FiArrowRight,
  FiCheckCircle,
  FiMessageSquare,
  FiSliders,
} from "react-icons/fi";
import { GiArtificialHive } from "react-icons/gi";
import { BsStars } from "react-icons/bs";
import { LoginModal } from "../components/LoginModel";

export default function Home({ user, setUser }) {
  const [showLoginModal, setShowLoginModal] = useState(false);

  return (
    <div className="bg-[#F8F9FB] text-slate-800 font-sans min-h-screen overflow-x-hidden selection:bg-indigo-100 selection:text-indigo-700">
      {/* ── NAVBAR ── */}
      <motion.nav
        initial={{ y: -60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="fixed top-0 left-0 right-0 z-50 h-[64px] flex items-center justify-between px-6 md:px-12 bg-white/80 backdrop-blur-xl border-b border-slate-100 shadow-2xs"
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <GiArtificialHive size={20} color="white" />
          </div>
          <span className="font-extrabold text-base tracking-tight text-slate-900">
            Fresher.Ai
          </span>
        </div>

        {/* Nav Buttons */}
        <div className="flex items-center gap-3">
          <motion.button
            onClick={() => setShowLoginModal(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 hover:bg-slate-50 transition-colors"
          >
            Log In
          </motion.button>
          <motion.button
            onClick={() => setShowLoginModal(true)}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-[#4F46E5] hover:bg-[#4338CA] text-white text-xs font-semibold shadow-sm shadow-indigo-500/25 transition-all"
          >
            Get Started Free →
          </motion.button>
        </div>
      </motion.nav>

      {/* ── HERO SECTION ── */}
      <section className="relative pt-28 pb-16 px-4 sm:px-6 md:px-8 max-w-6xl mx-auto">
        <div className="relative rounded-[32px] bg-gradient-to-r from-[#EEF2FF] via-[#F5F3FF] to-[#FAF5FF] border border-indigo-100/90 p-8 sm:p-12 md:p-14 shadow-[0_8px_32px_rgba(79,70,229,0.06)] overflow-hidden flex flex-col md:flex-row items-center justify-between gap-10">
          {/* Left Hero Content */}
          <div className="flex-1 max-w-xl z-10 text-left">
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/90 backdrop-blur-md border border-indigo-100 text-xs font-semibold text-slate-700 shadow-2xs mb-5">
              <span>👋 Welcome to Next-Gen Prep!</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-[1.12] mb-4">
              Ready to{" "}
              <span className="text-[#4F46E5] bg-gradient-to-r from-[#4F46E5] to-[#7C3AED] bg-clip-text text-transparent">
                ace
              </span>{" "}
              your next interview?
            </h1>

            <p className="text-slate-600 text-sm sm:text-base font-normal leading-relaxed mb-8">
              Practice with AI, improve your answers with real-time evaluation, and get personalized feedback to land your dream job.
            </p>

            <div className="flex flex-wrap items-center gap-4 sm:gap-6">
              <button
                onClick={() => setShowLoginModal(true)}
                className="flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-[#4F46E5] hover:bg-[#4338CA] text-white text-sm font-bold shadow-lg shadow-indigo-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <span>Start Practicing Now</span>
                <FiArrowRight size={16} />
              </button>

              <div className="flex items-center gap-2.5">
                <div className="flex -space-x-2">
                  <img
                    className="w-8 h-8 rounded-full border-2 border-white object-cover shadow-2xs"
                    src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&auto=format&fit=crop&q=80"
                    alt="Student"
                  />
                  <img
                    className="w-8 h-8 rounded-full border-2 border-white object-cover shadow-2xs"
                    src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&auto=format&fit=crop&q=80"
                    alt="Student"
                  />
                  <img
                    className="w-8 h-8 rounded-full border-2 border-white object-cover shadow-2xs"
                    src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&auto=format&fit=crop&q=80"
                    alt="Student"
                  />
                </div>
                <span className="text-xs font-medium text-slate-500">
                  <strong className="text-slate-800 font-bold">10K+</strong> students practicing every day
                </span>
              </div>
            </div>
          </div>

          {/* Right Hero Mascot Area */}
          <div className="relative w-full max-w-[280px] sm:max-w-[340px] aspect-square flex items-center justify-center shrink-0">
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-300/30 to-purple-400/30 blur-2xl transform scale-90" />

            <motion.div
              animate={{ y: [-4, 6, -4] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-4 left-2 z-20 w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-500/25 font-mono font-bold text-base"
            >
              &lt;/&gt;
            </motion.div>

            <motion.div
              animate={{ y: [6, -6, 6] }}
              transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-8 right-2 z-20 w-12 h-12 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-lg shadow-orange-500/25"
            >
              <FiMessageSquare size={20} />
            </motion.div>

            <div className="relative z-10 w-52 h-52 sm:w-64 sm:h-64 flex items-center justify-center">
              <svg
                viewBox="0 0 200 200"
                className="w-full h-full drop-shadow-xl"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <ellipse cx="100" cy="165" rx="42" ry="18" fill="#CBD5E1" opacity="0.5" />
                <rect x="65" y="110" width="70" height="50" rx="20" fill="url(#home_bot_body)" />
                <rect x="75" y="122" width="50" height="24" rx="10" fill="#0F172A" />
                <circle cx="90" cy="134" r="3" fill="#60A5FA" />
                <circle cx="100" cy="134" r="3" fill="#34D399" />
                <circle cx="110" cy="134" r="3" fill="#F472B6" />
                <rect x="90" y="98" width="20" height="15" rx="4" fill="#94A3B8" />
                <rect x="52" y="45" width="96" height="60" rx="24" fill="url(#home_bot_head)" stroke="#FFFFFF" strokeWidth="3" />
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
                  <linearGradient id="home_bot_head" x1="52" y1="45" x2="148" y2="105" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#F8FAFC" />
                    <stop offset="1" stopColor="#E2E8F0" />
                  </linearGradient>
                  <linearGradient id="home_bot_body" x1="65" y1="110" x2="135" y2="160" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#FFFFFF" />
                    <stop offset="1" stopColor="#E2E8F0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>

        {/* ── 3 Practice Tracks ── */}
        <div className="mt-14 space-y-4">
          <div className="text-center max-w-xl mx-auto mb-8">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Start an Interview in Seconds
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Choose your practice track and let AI conduct realistic mock interviews.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div
              onClick={() => setShowLoginModal(true)}
              className="bg-white rounded-3xl border border-indigo-100 p-6 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="flex items-start gap-4 mb-8">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-mono font-bold text-lg shadow-sm shrink-0">
                  &lt;/&gt;
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    Technical Interview
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    Practice DSA, system design, coding problems and technical concepts.
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <div className="w-9 h-9 rounded-full border border-slate-200 group-hover:bg-indigo-600 group-hover:text-white text-slate-400 flex items-center justify-center transition">
                  <FiArrowRight size={15} />
                </div>
              </div>
            </div>

            <div
              onClick={() => setShowLoginModal(true)}
              className="bg-white rounded-3xl border border-orange-100 p-6 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="flex items-start gap-4 mb-8">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-sm shrink-0">
                  <FiMessageSquare size={24} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-orange-600 transition-colors">
                    HR &amp; Behavioral
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    Prepare for situational, behavioral, and communication rounds.
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <div className="w-9 h-9 rounded-full border border-slate-200 group-hover:bg-orange-500 group-hover:text-white text-slate-400 flex items-center justify-center transition">
                  <FiArrowRight size={15} />
                </div>
              </div>
            </div>

            <div
              onClick={() => setShowLoginModal(true)}
              className="bg-white rounded-3xl border border-emerald-100 p-6 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="flex items-start gap-4 mb-8">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-500 text-white flex items-center justify-center shadow-sm shrink-0">
                  <BsStars size={24} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
                    Custom Interview
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    Tailor questions to your exact job role, resume, and experience level.
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <div className="w-9 h-9 rounded-full border border-slate-200 group-hover:bg-emerald-500 group-hover:text-white text-slate-400 flex items-center justify-center transition">
                  <FiArrowRight size={15} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-slate-200/80 py-8 text-center text-xs text-slate-400 bg-white">
        <p>© 2026 Fresher.Ai • AI Multi-Agent Interview &amp; Career Preparation</p>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          setUser={setUser}
        />
      )}
    </div>
  );
}