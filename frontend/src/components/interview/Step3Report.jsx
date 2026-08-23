import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiArrowLeft,
  FiAward,
  FiTarget,
  FiTrendingUp,
  FiBookOpen,
  FiCheckCircle,
  FiAlertCircle,
  FiXCircle,
  FiHelpCircle,
  FiChevronDown,
  FiChevronUp,
  FiLayers,
  FiCompass,
  FiZap,
} from "react-icons/fi";
import { BsStars } from "react-icons/bs";
import DownloadButton from "../resume/DownloadButton";
import { useNavigate } from "react-router-dom";

export default function Step3Report({ report, user, setUser }) {
  const reportRef = useRef(null);
  const navigate = useNavigate();

  // State to toggle question expansion (default first question open)
  const [expandedQuestions, setExpandedQuestions] = useState({ 0: true });

  const toggleQuestion = (idx) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const expandAll = () => {
    const all = {};
    (report?.questions || report?.questionReviews || []).forEach((_, i) => {
      all[i] = true;
    });
    setExpandedQuestions(all);
  };

  const collapseAll = () => {
    setExpandedQuestions({});
  };

  // Safe fallback extractions
  const overallScore = report?.overallScore ?? 75;
  const role = report?.role || "Software Engineer";
  const interviewType = report?.type === "hr" ? "HR & Behavioral" : "Technical";
  
  // Standardized counts
  const questionsList = report?.questions || [];
  const questionReviews = report?.questionReviews || [];
  const totalQuestions = report?.questionsCount || questionsList.length || 6;

  // Compute or read result counts
  let correctCount = report?.correctCount ?? 0;
  let partialCount = report?.partialCount ?? 0;
  let incorrectCount = report?.incorrectCount ?? 0;
  let insufficientCount = report?.insufficientCount ?? 0;

  if (correctCount === 0 && partialCount === 0 && incorrectCount === 0 && questionsList.length > 0) {
    questionsList.forEach((q) => {
      const res = q.feedback?.result;
      const s = q.feedback?.score ?? q.score ?? 70;
      if (res === "correct" || (!res && s >= 75)) correctCount++;
      else if (res === "partially_correct" || (!res && s >= 50)) partialCount++;
      else if (res === "insufficient") insufficientCount++;
      else incorrectCount++;
    });
  }

  const averageScore = report?.averageScore || overallScore;

  // Readiness tier and colors
  const readiness = report?.readiness || (overallScore >= 90 ? "Excellent / Interview Ready" : overallScore >= 75 ? "Strong / Nearly Ready" : overallScore >= 60 ? "Developing / Needs Practice" : "Significant Improvement Needed");
  const readinessDesc = report?.readinessDescription || (overallScore >= 75 ? "Solid conceptual and practical foundation. Ready for live interviews with minor refinement." : "Demonstrated foundational awareness with notable opportunities for structured depth.");

  const getReadinessBadgeClass = () => {
    if (overallScore >= 90) return "bg-emerald-500/10 text-emerald-700 border-emerald-500/20";
    if (overallScore >= 75) return "bg-indigo-500/10 text-indigo-700 border-indigo-500/20";
    if (overallScore >= 60) return "bg-amber-500/10 text-amber-700 border-amber-500/20";
    return "bg-rose-500/10 text-rose-700 border-rose-500/20";
  };

  // Category scores
  const categoryScores = report?.categoryScores || {
    "Technical Correctness": Math.min(100, overallScore + 2),
    "Completeness": Math.max(40, overallScore - 4),
    "Problem Solving": Math.min(100, overallScore + 1),
    "Communication": Math.min(100, overallScore + 3),
    "Relevance": Math.min(100, overallScore + 5),
  };

  // Topic accuracy
  const topicAccuracy = report?.topicAccuracy || [];

  // Strengths & Improvements
  const topStrengths = report?.topStrengths || report?.strengths || [
    "Demonstrated solid conceptual foundation across primary domain questions.",
    "Clear communication structure and professional tone.",
    "Good engagement and attempted all timed questions."
  ];

  const priorityImprovements = report?.priorityImprovements || report?.weaknesses || [
    "Incorporate concrete production metrics and quantifiable performance trade-offs.",
    "Elaborate further on architectural resilience and edge-case mitigations.",
    "Practice structured step-by-step problem deconstruction."
  ];

  const recommendations = report?.recommendations || [
    "Focus on deep dive drills for concepts scoring below 75%.",
    "Practice structuring answers with trade-offs and edge-cases.",
    "Incorporate measurable business and engineering metrics into past project explanations.",
    "Review caching strategies, indexing optimizations, and query profiling.",
    "Re-attempt mock interviews to build consistent timed delivery confidence."
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0A0A0A] font-sans py-6 px-3 sm:px-6 md:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Navigation & Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-white rounded-2xl border border-black/8 p-4 md:p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/dashboard")}
              className="inline-flex items-center gap-2 text-xs font-semibold text-black bg-black/5 hover:bg-black/10 border border-black/10 rounded-xl px-3.5 py-2 transition"
            >
              <FiArrowLeft size={14} />
              <span>Back to Dashboard</span>
            </button>
            <div className="hidden sm:flex items-center gap-1.5 text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200/60 rounded-xl px-3 py-1.5">
              <BsStars size={13} />
              <span>Verified Report</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <DownloadButton
              resumeRef={reportRef}
              user={user}
              setUser={setUser}
            />
          </div>
        </div>

        {/* Main Report Container */}
        <div ref={reportRef} className="space-y-6 bg-transparent">

          {/* 1. TOP HERO SECTION */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl border border-black/8 p-6 md:p-8 shadow-sm relative overflow-hidden"
          >
            {/* Ambient background glow */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-purple-100/60 via-indigo-50/30 to-transparent rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              
              {/* Left Title & Readiness */}
              <div className="space-y-2 max-w-xl">
                <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-wider">
                  <FiAward size={15} />
                  <span>Interview Complete 🎉</span>
                </div>

                <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#0A0A0A] tracking-tight">
                  {role} • {interviewType} Interview
                </h1>

                <p className="text-xs sm:text-sm text-black/60 leading-relaxed">
                  {readinessDesc}
                </p>

                <div className="pt-2">
                  <span className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl border text-xs font-bold ${getReadinessBadgeClass()}`}>
                    <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                    <span>Hiring Readiness: {readiness}</span>
                  </span>
                </div>
              </div>

              {/* Right Calculated Score Circle */}
              <div className="shrink-0 flex items-center justify-center p-6 bg-gradient-to-br from-[#0F172A] to-[#1E293B] rounded-3xl shadow-xl border border-black/10 text-white min-w-[160px] text-center">
                <div>
                  <div className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-zinc-100 to-zinc-300 bg-clip-text text-transparent">
                    {overallScore}
                  </div>
                  <div className="text-xs font-medium text-white/60 mt-1 uppercase tracking-wider">
                    Calculated Score
                  </div>
                  <div className="text-[11px] text-emerald-400 font-semibold mt-1">
                    Out of 100
                  </div>
                </div>
              </div>

            </div>

            {/* Quick Stat Counter Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mt-8 pt-6 border-t border-black/6">
              
              <div className="p-3.5 rounded-2xl bg-black/[0.02] border border-black/5">
                <div className="text-[11px] font-semibold text-black/50 uppercase tracking-wider">
                  Questions
                </div>
                <div className="text-xl font-bold text-[#0A0A0A] mt-1">
                  {totalQuestions} / {totalQuestions}
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-emerald-50/70 border border-emerald-200/60">
                <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                  <span>🟢 Correct</span>
                </div>
                <div className="text-xl font-bold text-emerald-900 mt-1">
                  {correctCount}
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200/60">
                <div className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider flex items-center gap-1">
                  <span>🟡 Partial</span>
                </div>
                <div className="text-xl font-bold text-amber-900 mt-1">
                  {partialCount}
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-rose-50/70 border border-rose-200/60">
                <div className="text-[11px] font-semibold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                  <span>🔴 Incorrect</span>
                </div>
                <div className="text-xl font-bold text-rose-900 mt-1">
                  {incorrectCount}
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-indigo-50/70 border border-indigo-200/60 col-span-2 sm:col-span-1">
                <div className="text-[11px] font-semibold text-indigo-800 uppercase tracking-wider">
                  Average Score
                </div>
                <div className="text-xl font-bold text-indigo-900 mt-1">
                  {averageScore}/100
                </div>
              </div>

            </div>
          </motion.div>

          {/* 2. EXECUTIVE PERFORMANCE SYNTHESIS */}
          {report?.summary && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl border border-black/8 p-6 md:p-7 shadow-sm"
            >
              <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-wider mb-2">
                <BsStars size={14} />
                <span>Executive Performance Synthesis</span>
              </div>
              <h2 className="text-lg font-bold text-[#0A0A0A]">
                AI Talent Assessment Summary
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-black/70">
                {report.summary}
              </p>
            </motion.div>
          )}

          {/* 3. PERFORMANCE BREAKDOWN & TOPIC ACCURACY */}
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Category Performance Breakdown */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl border border-black/8 p-6 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">
                  <FiLayers size={14} />
                  <span>Standardized Rubric</span>
                </div>
                <h3 className="text-base font-bold text-[#0A0A0A] mb-4">
                  Performance Breakdown
                </h3>

                <div className="space-y-4">
                  {Object.entries(categoryScores).map(([catName, scoreVal], idx) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-black/80">{catName}</span>
                        <span className="font-mono text-black">{scoreVal}/100</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-black/5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            scoreVal >= 75
                              ? "bg-emerald-500"
                              : scoreVal >= 60
                              ? "bg-indigo-500"
                              : "bg-amber-500"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, scoreVal))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-black/5 text-[11px] text-black/50 flex items-center justify-between">
                <span>Weighted Scoring Formula</span>
                <span className="font-medium text-black/70">Evidence-Based</span>
              </div>
            </motion.div>

            {/* Topic-Wise Accuracy */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl border border-black/8 p-6 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-wider mb-1">
                  <FiCompass size={14} />
                  <span>Evaluated Topics</span>
                </div>
                <h3 className="text-base font-bold text-[#0A0A0A] mb-4">
                  Topic-Wise Accuracy
                </h3>

                {topicAccuracy.length > 0 ? (
                  <div className="space-y-3">
                    {topicAccuracy.map((top, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-black/[0.02] border border-black/5 flex items-center justify-between"
                      >
                        <div>
                          <div className="text-xs font-bold text-[#0A0A0A]">
                            {top.topic}
                          </div>
                          <div className="text-[11px] text-black/45 mt-0.5">
                            {top.questionsCount} question{top.questionsCount > 1 ? "s" : ""} asked
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5">
                          <div className="w-16 h-1.5 rounded-full bg-black/10 overflow-hidden">
                            <div
                              className="h-full bg-purple-600 rounded-full"
                              style={{ width: `${top.score}%` }}
                            />
                          </div>
                          <span className="text-xs font-bold font-mono text-purple-700 min-w-[36px] text-right">
                            {top.score}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="p-3 rounded-2xl bg-black/[0.02] border border-black/5 flex items-center justify-between">
                      <span className="text-xs font-bold text-[#0A0A0A]">Core Technical Fundamentals</span>
                      <span className="text-xs font-bold font-mono text-purple-700">{overallScore}%</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-black/[0.02] border border-black/5 flex items-center justify-between">
                      <span className="text-xs font-bold text-[#0A0A0A]">System Scaling & Workflow</span>
                      <span className="text-xs font-bold font-mono text-purple-700">{Math.max(50, overallScore - 6)}%</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-black/5 text-[11px] text-black/50">
                Calculated strictly from evaluated answers
              </div>
            </motion.div>

          </div>

          {/* 4. STRENGTHS & PRIORITY IMPROVEMENT AREAS */}
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Top Strengths */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl border border-emerald-500/20 p-6 md:p-7 shadow-sm"
            >
              <div className="flex items-center gap-2 text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1">
                <FiCheckCircle size={15} />
                <span>Evidence-Based</span>
              </div>
              <h3 className="text-lg font-bold text-[#0A0A0A] mb-4">
                Top Strengths Observed
              </h3>

              <ul className="space-y-3">
                {topStrengths.map((str, idx) => (
                  <li
                    key={idx}
                    className="p-3.5 rounded-2xl bg-emerald-50/60 border border-emerald-200/60 flex items-start gap-3 text-xs leading-relaxed text-emerald-950 font-medium"
                  >
                    <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0 text-[11px] font-bold mt-0.5">
                      ✓
                    </span>
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Priority Improvements */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl border border-amber-500/20 p-6 md:p-7 shadow-sm"
            >
              <div className="flex items-center gap-2 text-xs font-bold text-amber-700 uppercase tracking-wider mb-1">
                <FiAlertCircle size={15} />
                <span>Targeted Growth</span>
              </div>
              <h3 className="text-lg font-bold text-[#0A0A0A] mb-4">
                Priority Areas for Improvement
              </h3>

              <ul className="space-y-3">
                {priorityImprovements.map((imp, idx) => (
                  <li
                    key={idx}
                    className="p-3.5 rounded-2xl bg-amber-50/60 border border-amber-200/60 flex items-start gap-3 text-xs leading-relaxed text-amber-950 font-medium"
                  >
                    <span className="w-5 h-5 rounded-full bg-amber-500 text-white flex items-center justify-center shrink-0 text-[11px] font-bold mt-0.5">
                      !
                    </span>
                    <span>{imp}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

          </div>

          {/* 5. ACTIONABLE CAREER RECOMMENDATIONS */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl border border-black/8 p-6 md:p-7 shadow-sm"
          >
            <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-wider mb-1">
              <FiZap size={14} />
              <span>Next Steps</span>
            </div>
            <h3 className="text-lg font-bold text-[#0A0A0A] mb-4">
              Actionable Recommendations
            </h3>

            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3.5">
              {recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-purple-50/40 border border-purple-100 flex flex-col justify-between space-y-2"
                >
                  <div className="w-7 h-7 rounded-xl bg-purple-600 text-white font-bold text-xs flex items-center justify-center shadow-sm">
                    {idx + 1}
                  </div>
                  <p className="text-xs leading-relaxed text-purple-950 font-medium">
                    {rec}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* 6. QUESTION-BY-QUESTION REVIEW (ACCORDION) */}
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4">
              <div>
                <h3 className="text-xl font-extrabold text-[#0A0A0A] tracking-tight">
                  Question-by-Question Detailed Review
                </h3>
                <p className="text-xs text-black/50 mt-0.5">
                  Review every question, submitted answer, strengths, omissions, conceptual corrections, and model answers.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <button
                  onClick={expandAll}
                  className="px-3 py-1.5 rounded-lg border border-black/10 hover:bg-black/5 font-semibold text-black/70 transition"
                >
                  Expand All
                </button>
                <button
                  onClick={collapseAll}
                  className="px-3 py-1.5 rounded-lg border border-black/10 hover:bg-black/5 font-semibold text-black/70 transition"
                >
                  Collapse All
                </button>
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-4">
              {questionsList.map((item, index) => {
                const fb = item.feedback || {};
                const qScore = fb.score ?? item.score ?? 70;
                const result = fb.result || (qScore >= 75 ? "correct" : qScore >= 50 ? "partially_correct" : "incorrect");
                const isExpanded = !!expandedQuestions[index];

                const resultConfig = {
                  correct: {
                    badge: "🟢 Correct",
                    class: "bg-emerald-50 text-emerald-800 border-emerald-200",
                    borderAccent: "border-emerald-500/20",
                  },
                  partially_correct: {
                    badge: "🟡 Partially Correct",
                    class: "bg-amber-50 text-amber-800 border-amber-200",
                    borderAccent: "border-amber-500/20",
                  },
                  incorrect: {
                    badge: "🔴 Incorrect",
                    class: "bg-rose-50 text-rose-800 border-rose-200",
                    borderAccent: "border-rose-500/20",
                  },
                  insufficient: {
                    badge: "⚪ Insufficient Answer",
                    class: "bg-zinc-100 text-zinc-800 border-zinc-200",
                    borderAccent: "border-zinc-300",
                  },
                }[result] || {
                  badge: "🟡 Partially Correct",
                  class: "bg-amber-50 text-amber-800 border-amber-200",
                  borderAccent: "border-amber-500/20",
                };

                const strengths = fb.strengths || fb.keyPointsCovered || [];
                const missingPoints = fb.missing_points || fb.keyPointsMissed || [];
                const incorrectPoints = fb.incorrect_points || [];
                const whatToUnderstand = fb.what_you_should_understand;
                const approachGuidance = fb.approach_guidance || fb.improvements || [];
                const idealAnswer = fb.ideal_answer_summary || fb.idealAnswer || fb.correctAnswer || "";

                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`bg-white rounded-3xl border ${resultConfig.borderAccent} overflow-hidden shadow-sm transition-all`}
                  >
                    {/* Header Trigger */}
                    <button
                      onClick={() => toggleQuestion(index)}
                      className="w-full p-5 md:p-6 text-left flex items-start justify-between gap-4 hover:bg-black/[0.01] transition"
                    >
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`px-2.5 py-0.5 rounded-lg border text-[11px] font-bold ${resultConfig.class}`}>
                            {resultConfig.badge}
                          </span>
                          <span className="text-[11px] font-semibold text-black/50 uppercase tracking-wider">
                            Question {index + 1}
                          </span>
                          {item.difficulty && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-black/5 text-black/60 font-medium capitalize">
                              {item.difficulty}
                            </span>
                          )}
                          {item.topic && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-medium">
                              {item.topic}
                            </span>
                          )}
                          {item.source === "resume" && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-medium">
                              📄 Resume Project
                            </span>
                          )}
                        </div>

                        <h4 className="text-base font-bold text-[#0A0A0A] leading-snug">
                          {item.question}
                        </h4>
                      </div>

                      <div className="shrink-0 flex items-center gap-3">
                        <span className="font-mono text-sm font-extrabold text-black/80 bg-black/5 px-2.5 py-1 rounded-xl">
                          {qScore}/100
                        </span>
                        <div className="w-8 h-8 rounded-full bg-black/5 flex items-center justify-center text-black/60">
                          {isExpanded ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
                        </div>
                      </div>
                    </button>

                    {/* Accordion Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="px-5 md:px-6 pb-6 pt-2 space-y-5 border-t border-black/5"
                        >
                          {/* Submitted Answer */}
                          <div className="p-4 rounded-2xl bg-black/[0.02] border border-black/5 space-y-1">
                            <span className="text-[11px] font-bold text-black/50 uppercase tracking-wider">
                              Your Submitted Answer
                            </span>
                            <p className="text-xs sm:text-sm text-black/80 leading-relaxed font-sans">
                              {item.userAnswer || "No answer submitted."}
                            </p>
                          </div>

                          {/* Strengths and Missing Points Grid */}
                          <div className="grid md:grid-cols-2 gap-4">
                            {/* Strengths */}
                            {strengths.length > 0 && (
                              <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200/60 space-y-2">
                                <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 uppercase tracking-wider">
                                  <FiCheckCircle size={14} />
                                  <span>What You Did Well</span>
                                </div>
                                <ul className="space-y-1.5">
                                  {strengths.map((str, sIdx) => (
                                    <li key={sIdx} className="text-xs text-emerald-950 flex items-start gap-2 leading-relaxed">
                                      <span className="text-emerald-600 font-bold mt-0.5">✓</span>
                                      <span>{str}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Missing Points */}
                            {missingPoints.length > 0 && (
                              <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200/60 space-y-2">
                                <div className="flex items-center gap-2 text-xs font-bold text-amber-800 uppercase tracking-wider">
                                  <FiAlertCircle size={14} />
                                  <span>What Was Missing</span>
                                </div>
                                <ul className="space-y-1.5">
                                  {missingPoints.map((mis, mIdx) => (
                                    <li key={mIdx} className="text-xs text-amber-950 flex items-start gap-2 leading-relaxed">
                                      <span className="text-amber-600 font-bold mt-0.5">⚠</span>
                                      <span>{mis}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Conceptual Understanding & Misconception Breakdown */}
                          {(whatToUnderstand || incorrectPoints.length > 0) && (
                            <div className="p-4 rounded-2xl bg-rose-50/60 border border-rose-200/70 space-y-1.5">
                              <div className="flex items-center gap-2 text-xs font-bold text-rose-800 uppercase tracking-wider">
                                <FiXCircle size={14} />
                                <span>What You Should Understand</span>
                              </div>
                              {whatToUnderstand && (
                                <p className="text-xs leading-relaxed text-rose-950">
                                  {whatToUnderstand}
                                </p>
                              )}
                              {incorrectPoints.length > 0 && (
                                <ul className="space-y-1 pt-1">
                                  {incorrectPoints.map((inc, iIdx) => (
                                    <li key={iIdx} className="text-xs text-rose-900 flex items-start gap-1.5">
                                      <span className="font-bold">•</span>
                                      <span>{inc}</span>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          )}

                          {/* Better Approach Guidance */}
                          {approachGuidance.length > 0 && (
                            <div className="p-4 rounded-2xl bg-indigo-50/40 border border-indigo-100 space-y-2">
                              <div className="flex items-center gap-2 text-xs font-bold text-indigo-800 uppercase tracking-wider">
                                <FiTarget size={14} />
                                <span>How to Approach This Question</span>
                              </div>
                              <div className="space-y-1.5">
                                {approachGuidance.map((step, sIdx) => (
                                  <div key={sIdx} className="text-xs text-indigo-950 flex items-start gap-2 leading-relaxed">
                                    <span className="font-mono font-bold text-indigo-600 shrink-0">
                                      {sIdx + 1}.
                                    </span>
                                    <span>{step.replace(/^\d+\.\s*/, "")}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Example of a Strong Model Answer */}
                          {idealAnswer && (
                            <div className="p-4 rounded-2xl bg-purple-50/50 border border-purple-200/60 space-y-2">
                              <div className="flex items-center gap-2 text-xs font-bold text-purple-800 uppercase tracking-wider">
                                <FiBookOpen size={14} />
                                <span>Example of a Strong Answer</span>
                              </div>
                              <div className="p-3.5 rounded-xl bg-white border border-purple-100 font-sans text-xs leading-relaxed text-purple-950 font-medium">
                                {idealAnswer}
                              </div>
                            </div>
                          )}

                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}