import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiTarget,
  FiClock,
  FiCheckCircle,
  FiArrowLeft,
  FiExternalLink,
  FiLayers,
  FiBookOpen,
  FiPlayCircle,
  FiBriefcase,
  FiTool,
  FiCheck,
  FiAlertCircle,
  FiChevronDown,
  FiChevronUp,
  FiCpu,
  FiCode,
} from "react-icons/fi";
import { TechLogo } from "../../utils/logoResolver";
import YouTubeLearningSection from "./YouTubeLearningSection";

export default function RoadmapResult({ roadmap, onClear }) {
  // Extract normalized data from Section 10 schema or legacy aliases
  const tools = roadmap.tools || roadmap.essentialTools || roadmap.essential_tools || [];
  const youtubeList = roadmap.youtube_resources || roadmap.youtubePlaylists || roadmap.youtube_playlists || [];
  const docsList = roadmap.official_docs || roadmap.learningResources || roadmap.learning_resources || [];
  const careerList = roadmap.career_resources || roadmap.careerResources || [];
  const modules = roadmap.modules || [];

  // Skill gap data for candidate resume integration
  const rawSkills = roadmap.skills || {};
  const strongSkills = rawSkills.strong || roadmap.skillGapSummary?.strongSkills || [];
  const partialSkills = rawSkills.partial || roadmap.skillGapSummary?.partialSkills || [];
  const missingSkills = rawSkills.missing || roadmap.skillGapSummary?.missingSkills || [];
  const prioritySkills = rawSkills.priority || roadmap.skillGapSummary?.prioritySkills || [];

  const isPersonalized = Boolean(
    roadmap.summary?.personalized ||
    roadmap.personalized ||
    strongSkills.length > 0 ||
    partialSkills.length > 0
  );

  const durationWeeks = roadmap.summary?.duration_weeks || roadmap.duration || `${modules.length} Weeks`;
  const difficultyLevel = roadmap.summary?.difficulty || roadmap.level || "Beginner Friendly";
  const targetSalary = roadmap.target_salary || roadmap.targetPackage || roadmap.package || "15 LPA";
  const roleTitle = roadmap.role || roadmap.title || "Software Engineering Career Roadmap";

  const [expandedWeek, setExpandedWeek] = useState(0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* ── 1. HEADER OVERVIEW CARD ── */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-[11px] font-bold text-indigo-700 mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse" />
              {isPersonalized ? "Personalized Career Path" : "Canonical Knowledge Roadmap"}
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {roleTitle}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Target Compensation:{" "}
              <span className="text-indigo-600 font-bold">{targetSalary}</span>
            </p>
          </div>

          <button
            onClick={onClear}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition self-start cursor-pointer shadow-2xs"
          >
            <FiArrowLeft size={13} />
            <span>New Roadmap</span>
          </button>
        </div>

        {/* 3 Metric Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <div className="rounded-2xl p-4 bg-purple-50/60 border border-purple-100/80 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
              <FiTarget size={18} />
            </div>
            <div>
              <p className="text-[11px] font-medium text-purple-600 uppercase tracking-wider">Level</p>
              <p className="text-sm font-bold text-slate-900">{difficultyLevel}</p>
            </div>
          </div>

          <div className="rounded-2xl p-4 bg-blue-50/60 border border-blue-100/80 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
              <FiClock size={18} />
            </div>
            <div>
              <p className="text-[11px] font-medium text-blue-600 uppercase tracking-wider">Duration</p>
              <p className="text-sm font-bold text-slate-900">{durationWeeks}</p>
            </div>
          </div>

          <div className="rounded-2xl p-4 bg-emerald-50/60 border border-emerald-100/80 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <FiCheckCircle size={18} />
            </div>
            <div>
              <p className="text-[11px] font-medium text-emerald-600 uppercase tracking-wider">Curated Resources</p>
              <p className="text-sm font-bold text-slate-900">
                {tools.length + youtubeList.length + docsList.length + careerList.length} Verified
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. RESUME SKILL-GAP COMPARISON BANNER (Only if resume personalized) ── */}
      {isPersonalized && (
        <div className="bg-slate-900 text-white rounded-3xl p-6 sm:p-7 shadow-md space-y-4 border border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3.5">
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Resume-Personalized Skill Gap Profile
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Your roadmap has been personalized based on your resume. Strong skills are fast-tracked, while high-priority gaps are prioritized.
              </p>
            </div>
            <span className="text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full self-start sm:self-auto">
              Fast-Track Enabled
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            {/* Strong Skills */}
            <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/60">
              <p className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5 mb-2.5">
                <FiCheck size={13} className="stroke-[3]" /> YOUR SKILLS (FAST-TRACKED)
              </p>
              {strongSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {strongSkills.map((s, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-200"
                    >
                      ✓ {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">None detected</p>
              )}
            </div>

            {/* Needs Improvement / Partial */}
            <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/60">
              <p className="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5 mb-2.5">
                <span className="text-amber-400 text-xs">◐</span> NEEDS IMPROVEMENT
              </p>
              {partialSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {partialSkills.map((s, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-200"
                    >
                      ◐ {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">None detected</p>
              )}
            </div>

            {/* Missing Skills */}
            <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/60">
              <p className="text-[11px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5 mb-2.5">
                <FiAlertCircle size={13} /> MISSING (HIGH PRIORITY)
              </p>
              {missingSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {missingSkills.map((s, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-200"
                    >
                      ! {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">None detected</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── 3. FOUR COMPACT RESOURCE DASHBOARD SECTIONS ── */}

      {/* Section A: Tools & Technologies */}
      {tools.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <FiTool size={15} />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Tools & Technologies
              </h3>
            </div>
            <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-3 py-0.5 rounded-full">
              {tools.length} Tools
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {tools.map((tool, idx) => {
              const name = tool.name || tool.tool_name || "Tool";
              const key = tool.logo_key || name;
              const cat = tool.category || "Development";
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200/80 bg-slate-50/40 hover:bg-white hover:border-indigo-300 p-3.5 flex items-center justify-between gap-3 transition shadow-2xs hover:shadow-xs group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-200/80 flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform">
                      <TechLogo logoKey={key} name={name} size={20} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate group-hover:text-indigo-600 transition-colors">
                        {name}
                      </p>
                      <p className="text-[10px] font-semibold text-slate-400 truncate">
                        {cat}
                      </p>
                    </div>
                  </div>

                  {tool.url && (
                    <a
                      href={tool.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 shrink-0 px-2 py-1 rounded-lg hover:bg-indigo-50 transition"
                      title={`Visit ${name}`}
                    >
                      <span>Visit</span>
                      <FiExternalLink size={11} />
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Section B: Curated YouTube Learning Resources */}
      {youtubeList.length > 0 && (
        <YouTubeLearningSection creators={youtubeList} />
      )}


      {/* Section C: Official Documentation */}
      {docsList.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <FiBookOpen size={15} />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Official Documentation
              </h3>
            </div>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-0.5 rounded-full">
              {docsList.length} Official Docs
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {docsList.map((doc, idx) => {
              const name = doc.title || doc.name || "Documentation";
              const key = doc.logo_key || name;
              const source = doc.source || doc.category || "Official Docs";
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200/80 bg-slate-50/40 hover:bg-white hover:border-emerald-300 p-3.5 flex items-center justify-between gap-3 transition shadow-2xs hover:shadow-xs group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-200/80 flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform">
                      <TechLogo logoKey={key} name={name} size={20} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate group-hover:text-emerald-600 transition-colors">
                        {name}
                      </p>
                      <p className="text-[10px] font-semibold text-slate-400 truncate">
                        {source}
                      </p>
                    </div>
                  </div>

                  {doc.url && (
                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 hover:text-emerald-800 shrink-0 px-2 py-1 rounded-lg hover:bg-emerald-50 transition"
                      title={`Open ${name}`}
                    >
                      <span>Open</span>
                      <FiExternalLink size={11} />
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Section D: Career / Practice Platforms */}
      {careerList.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                <FiBriefcase size={15} />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Career & Practice Platforms
              </h3>
            </div>
            <span className="text-[11px] font-bold text-sky-700 bg-sky-50 border border-sky-200 px-3 py-0.5 rounded-full">
              {careerList.length} Career Platforms
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {careerList.map((platform, idx) => {
              const name = platform.title || platform.name || "Platform";
              const key = platform.logo_key || name;
              const purpose = platform.purpose || platform.category || "Practice & Projects";
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200/80 bg-slate-50/40 hover:bg-white hover:border-sky-300 p-3.5 flex items-center justify-between gap-3 transition shadow-2xs hover:shadow-xs group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-200/80 flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform">
                      <TechLogo logoKey={key} name={name} size={20} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate group-hover:text-sky-600 transition-colors">
                        {name}
                      </p>
                      <p className="text-[10px] font-semibold text-slate-400 truncate">
                        {purpose}
                      </p>
                    </div>
                  </div>

                  {platform.url && (
                    <a
                      href={platform.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-600 hover:text-sky-800 shrink-0 px-2 py-1 rounded-lg hover:bg-sky-50 transition"
                      title={`Open ${name}`}
                    >
                      <span>Open</span>
                      <FiExternalLink size={11} />
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 4. WEEK-BY-WEEK PROGRESSIVE LEARNING TIMELINE ── */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between px-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <FiLayers size={14} className="text-indigo-600" /> Week-by-Week Learning Path Timeline
          </p>
          <span className="text-xs text-slate-400">Expand any week for topics & project build</span>
        </div>

        <div className="space-y-3">
          {modules.map((mod, idx) => {
            const isExpanded = expandedWeek === idx;
            const weekNum = mod.week || idx + 1;
            const weekPadded = String(weekNum).padStart(2, "0");
            const skillsList = mod.skills && mod.skills.length > 0 ? mod.skills : (mod.topics ? mod.topics.slice(0, 3) : []);
            const projObj = mod.project || (mod.projects && mod.projects[0] ? { title: mod.projects[0] } : null);

            return (
              <div
                key={idx}
                className={`bg-white rounded-2xl border transition-all duration-200 overflow-hidden shadow-xs ${
                  isExpanded ? "border-indigo-300 ring-1 ring-indigo-100" : "border-slate-200/80 hover:border-slate-300"
                }`}
              >
                {/* Collapsed Header Bar */}
                <div
                  onClick={() => setExpandedWeek(isExpanded ? -1 : idx)}
                  className="p-4 sm:p-5 flex items-center justify-between gap-3 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 flex flex-col items-center justify-center shrink-0">
                      <span className="text-[9px] font-extrabold uppercase leading-none text-indigo-400">WK</span>
                      <span className="text-sm font-black leading-tight text-indigo-700">{weekPadded}</span>
                    </div>

                    <div className="min-w-0">
                      <h4 className="text-sm sm:text-base font-bold text-slate-900 truncate">
                        {mod.title}
                      </h4>
                      {/* Skill preview chips */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-1">
                        {skillsList.slice(0, 3).map((sk, sIdx) => (
                          <span
                            key={sIdx}
                            className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md"
                          >
                            ✓ {sk}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="hidden sm:inline-block text-[11px] font-semibold px-2.5 py-0.5 rounded-full border border-slate-200 text-slate-600 bg-slate-50">
                      {mod.difficulty || "Intermediate"}
                    </span>
                    <div className="w-7 h-7 rounded-lg bg-slate-50 border border-slate-200/60 flex items-center justify-center text-slate-400">
                      {isExpanded ? <FiChevronUp size={15} /> : <FiChevronDown size={15} />}
                    </div>
                  </div>
                </div>

                {/* Expanded Details Body */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="px-5 pb-5 pt-2 border-t border-slate-100 bg-slate-50/40 space-y-4">
                        {/* Topics */}
                        {mod.topics && mod.topics.length > 0 && (
                          <div>
                            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                              Core Focus Topics
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {mod.topics.map((top, tIdx) => (
                                <span
                                  key={tIdx}
                                  className="text-xs font-medium text-slate-700 bg-white border border-slate-200 px-2.5 py-1 rounded-lg shadow-2xs"
                                >
                                  ○ {top}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Project Deliverable */}
                        {projObj && (
                          <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-100/90 flex items-center justify-between gap-3">
                            <div>
                              <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">
                                Hands-on Deliverable
                              </p>
                              <p className="text-xs font-bold text-slate-900 mt-0.5">
                                Build: {projObj.title || projObj}
                              </p>
                            </div>
                            <span className="text-[10px] font-bold text-indigo-700 bg-white px-2 py-0.5 rounded-md border border-indigo-200 shrink-0">
                              {projObj.difficulty || "Practical"}
                            </span>
                          </div>
                        )}

                        {/* Module Resource Links */}
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          {mod.videoUrl && (
                            <a
                              href={mod.videoUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition shadow-2xs cursor-pointer"
                            >
                              <FiPlayCircle size={13} />
                              <span>Watch YouTube Guide</span>
                              <FiExternalLink size={10} />
                            </a>
                          )}
                          {mod.docUrl && (
                            <a
                              href={mod.docUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 transition shadow-2xs cursor-pointer"
                            >
                              <FiBookOpen size={13} />
                              <span>Official Documentation</span>
                              <FiExternalLink size={10} />
                            </a>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}