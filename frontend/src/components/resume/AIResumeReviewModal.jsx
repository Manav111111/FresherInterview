import React from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiX,
  FiAward,
  FiCheckCircle,
  FiAlertCircle,
  FiZap,
  FiTrendingUp,
  FiTarget,
  FiBookOpen,
} from "react-icons/fi";

export default function AIResumeReviewModal({ isOpen, onClose, loading, analysis }) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/60 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ duration: 0.3 }}
          className="relative w-full max-w-3xl max-h-[90vh] bg-[#0E1016] border border-white/15 rounded-2xl sm:rounded-[24px] overflow-hidden flex flex-col shadow-2xl"
        >
          {/* Top Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                <FiZap className="text-purple-400" size={16} />
              </div>
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  AI ATS Resume Evaluation
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Groq LLaMA 3.3
                  </span>
                </h2>
                <p className="text-xs text-white/50">Comprehensive ATS scoring & career readiness analysis</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition"
            >
              <FiX size={18} />
            </button>
          </div>

          {/* Modal Body */}
          <div className="p-6 overflow-y-auto space-y-6 flex-1 text-white">
            {loading ? (
              <div className="py-16 flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-12 h-12 rounded-full border-4 border-purple-500/20 border-t-purple-500 animate-spin" />
                <div>
                  <h3 className="text-sm font-semibold text-white">Analyzing Resume Content with AI...</h3>
                  <p className="text-xs text-white/40 mt-1 max-w-sm">
                    Evaluating keyword density, measurable achievements, technical skills, and ATS parsability.
                  </p>
                </div>
              </div>
            ) : analysis ? (
              <>
                {/* Score & Role Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Score Card */}
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex items-center gap-4">
                    <div className="relative w-16 h-16 rounded-full border-4 border-purple-500/30 flex items-center justify-center bg-purple-500/10 flex-shrink-0">
                      <span className="text-xl font-extrabold text-white">{analysis.score || 78}</span>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wider text-white/40 font-semibold">Overall ATS Score</p>
                      <p className="text-xs text-purple-300 mt-1">
                        {analysis.score >= 80 ? "✨ Excellent ATS Optimization" : "📈 Good foundation, needs optimization"}
                      </p>
                    </div>
                  </div>

                  {/* Suggested Role Card */}
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <FiTarget className="text-blue-400" size={20} />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wider text-white/40 font-semibold">Suggested Target Role</p>
                      <h4 className="text-sm font-bold text-white mt-0.5">
                        {analysis.suggestedRole || "Full Stack Developer"}
                      </h4>
                    </div>
                  </div>
                </div>

                {/* Professional Summary Assessment */}
                {analysis.summary && (
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-wider text-white/40 font-semibold mb-1">
                      Professional Summary Assessment
                    </p>
                    <p className="text-xs text-white/80 leading-relaxed italic">
                      "{analysis.summary}"
                    </p>
                  </div>
                )}

                {/* Strengths & Weaknesses Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Strengths */}
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-3">
                      <FiCheckCircle size={15} />
                      <span>Strong Points</span>
                    </div>
                    <ul className="space-y-2">
                      {(analysis.strengths || []).map((item, idx) => (
                        <li key={idx} className="text-xs text-zinc-300 flex items-start gap-2">
                          <span className="text-emerald-400 font-bold mt-0.5">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Weaknesses / Gaps */}
                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                    <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-3">
                      <FiAlertCircle size={15} />
                      <span>Areas for Improvement</span>
                    </div>
                    <ul className="space-y-2">
                      {(analysis.weaknesses || []).map((item, idx) => (
                        <li key={idx} className="text-xs text-zinc-300 flex items-start gap-2">
                          <span className="text-amber-400 font-bold mt-0.5">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Missing Skills */}
                {analysis.missingSkills?.length > 0 && (
                  <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-4">
                    <p className="text-xs uppercase tracking-wider text-purple-300 font-semibold mb-2.5">
                      Recommended Missing Skills to Add
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.missingSkills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-purple-500/20 border border-purple-500/30 text-xs text-purple-200"
                        >
                          + {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {analysis.recommendations?.length > 0 && (
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-wider text-white/40 font-semibold mb-3">
                      AI Actionable Recommendations
                    </p>
                    <div className="space-y-2">
                      {analysis.recommendations.map((rec, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 text-xs text-zinc-300">
                          <span className="w-5 h-5 rounded-full bg-white/10 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <p className="leading-relaxed">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="py-12 text-center text-white/40 text-xs">
                No analysis available. Click "Review with AI" to evaluate your resume.
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3.5 border-t border-white/10 bg-black/40 flex items-center justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-white text-black font-semibold text-xs hover:bg-white/90 transition"
            >
              Close &amp; Keep Editing
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
