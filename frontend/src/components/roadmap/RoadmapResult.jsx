import { motion } from "motion/react";
import {
  FiTarget, FiClock, FiCheckCircle, FiMap,
  FiArrowLeft, FiExternalLink, FiGlobe, FiLayers,
  FiBookOpen, FiCpu, FiCode, FiDatabase,
  FiServer, FiShield, FiTerminal, FiZap, FiBookmark, FiCloud
} from "react-icons/fi";
import {
  SiGithub, SiSupabase, SiFirebase, SiMongodb,
  SiDocker, SiPostgresql, SiRedis, SiPostman,
  SiFastapi, SiReact, SiNextdotjs, SiTailwindcss,
  SiVite, SiTypescript, SiKubernetes, SiTerraform,
  SiLinux, SiPython
} from "react-icons/si";

import ModuleCard from "./ModuleCard";

// Dynamic Tool Icon Matcher based on tool name
const getToolIcon = (name) => {
  const n = (name || "").toLowerCase();
  if (n.includes("github")) return <SiGithub className="text-slate-900" size={22} />;
  if (n.includes("supabase")) return <SiSupabase className="text-emerald-500" size={22} />;
  if (n.includes("firebase")) return <SiFirebase className="text-amber-500" size={22} />;
  if (n.includes("mongo")) return <SiMongodb className="text-green-600" size={22} />;
  if (n.includes("docker")) return <SiDocker className="text-blue-500" size={22} />;
  if (n.includes("postgres") || n.includes("sql")) return <SiPostgresql className="text-sky-600" size={22} />;
  if (n.includes("redis")) return <SiRedis className="text-rose-600" size={22} />;
  if (n.includes("postman")) return <SiPostman className="text-orange-500" size={22} />;
  if (n.includes("fastapi")) return <SiFastapi className="text-teal-600" size={22} />;
  if (n.includes("react")) return <SiReact className="text-cyan-500" size={22} />;
  if (n.includes("next")) return <SiNextdotjs className="text-slate-900" size={22} />;
  if (n.includes("tailwind")) return <SiTailwindcss className="text-sky-500" size={22} />;
  if (n.includes("vite")) return <SiVite className="text-purple-500" size={22} />;
  if (n.includes("typescript")) return <SiTypescript className="text-blue-600" size={22} />;
  if (n.includes("kubernetes")) return <SiKubernetes className="text-indigo-600" size={22} />;
  if (n.includes("terraform")) return <SiTerraform className="text-purple-600" size={22} />;
  if (n.includes("aws") || n.includes("cloud") || n.includes("amazon")) return <FiCloud className="text-amber-600" size={22} />;
  if (n.includes("linux") || n.includes("bash")) return <SiLinux className="text-slate-800" size={22} />;
  if (n.includes("python")) return <SiPython className="text-blue-500" size={22} />;
  if (n.includes("data") || n.includes("store")) return <FiDatabase className="text-sky-600" size={22} />;
  if (n.includes("server") || n.includes("api")) return <FiServer className="text-indigo-600" size={22} />;
  return <FiGlobe className="text-indigo-600" size={22} />;
};

export default function RoadmapResult({ roadmap, onClear }) {
  const tools = roadmap.essentialTools || roadmap.essential_tools || [];
  const syllabus = roadmap.syllabus || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* ── 1. Header Overview Card ── */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-[11px] font-bold text-indigo-600 mb-2">
              Generated Learning Path
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {roadmap.title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Target Compensation: <span className="text-indigo-600 font-bold">{roadmap.package || roadmap.targetPackage || "15+ LPA"}</span>
            </p>
          </div>

          <button
            onClick={onClear}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-200/80 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition cursor-pointer"
          >
            <FiArrowLeft size={13} />
            <span>New Roadmap</span>
          </button>
        </div>

        {/* 3 Metric Pills */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {[
            { icon: FiTarget,      label: "Difficulty", value: roadmap.level || "Intermediate", bg: "bg-purple-50 text-purple-600" },
            { icon: FiClock,       label: "Estimated Duration",   value: roadmap.duration || "12 Weeks", bg: "bg-blue-50 text-blue-600" },
            { icon: FiCheckCircle, label: "Total Modules",    value: `${roadmap.modules?.length || 0} Modules`, bg: "bg-emerald-50 text-emerald-600" },
          ].map(({ icon: Icon, label, value, bg }) => (
            <div key={label} className="rounded-2xl p-4 bg-slate-50/70 border border-slate-200/60 flex items-center gap-3.5">
              <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
                <Icon size={18} />
              </div>
              <div>
                <p className="text-[11px] font-medium text-slate-400">{label}</p>
                <p className="text-sm font-bold text-slate-900">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 2. Must-Visit Tools & Official Websites Section (Dynamic LLM) ── */}
      {tools.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <FiGlobe size={15} />
                </div>
                <h3 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
                  Essential Tools, Platforms & Official Websites
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Technologies, cloud services, and platforms generated specifically for this role to master and visit.
              </p>
            </div>
            <span className="text-[11px] font-semibold text-indigo-600 bg-indigo-50 border border-indigo-100 px-3 py-1 rounded-full self-start sm:self-auto">
              {tools.length} Must-Know Websites
            </span>
          </div>

          {/* Tools Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1">
            {tools.map((tool, idx) => (
              <motion.div
                key={tool.name || idx}
                whileHover={{ y: -2 }}
                transition={{ duration: 0.2 }}
                className="group rounded-2xl border border-slate-200/80 hover:border-indigo-300 bg-slate-50/50 hover:bg-white p-4 flex flex-col justify-between transition-all shadow-2xs hover:shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-200/80 flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform">
                      {getToolIcon(tool.name)}
                    </div>
                    {tool.tag && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {tool.tag}
                      </span>
                    )}
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {tool.name}
                  </h4>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">
                    {tool.category || "Platform"}
                  </p>
                  <p className="text-xs text-slate-600 mt-2 line-clamp-2 leading-relaxed">
                    {tool.description}
                  </p>
                </div>

                <div className="pt-4 mt-3 border-t border-slate-200/60">
                  <a
                    href={tool.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-xl bg-white group-hover:bg-indigo-600 border border-slate-200/80 group-hover:border-indigo-600 text-xs font-semibold text-slate-700 group-hover:text-white transition-all shadow-2xs cursor-pointer"
                  >
                    <span>Visit {tool.name}</span>
                    <FiExternalLink size={12} className="opacity-75 group-hover:opacity-100" />
                  </a>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 3. Core Syllabus & Pillars Breakdown (Dynamic LLM) ── */}
      {syllabus.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <FiBookmark size={15} />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
                Role Syllabus & Core Topic Pillars
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                AI-curated structured curriculum covering theoretical foundations, architecture, and production readiness.
              </p>
            </div>
          </div>

          {/* Syllabus Pillars Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {syllabus.map((item, idx) => (
              <div
                key={item.pillar || idx}
                className="p-5 rounded-2xl border border-slate-200/80 bg-slate-50/40 hover:bg-slate-50/80 transition-colors space-y-3"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {item.pillar}
                    </h4>
                    {item.description && (
                      <p className="text-xs text-slate-500 leading-snug mt-0.5">
                        {item.description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Topics Pills */}
                {item.topics && item.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {item.topics.map((topic) => (
                      <span
                        key={topic}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200/80 text-[11px] font-medium text-slate-700 shadow-2xs"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. Learning Path Milestones List ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1 pt-2">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <FiMap size={14} className="text-indigo-600" /> Week-by-Week Learning Path Milestones
          </p>
          <span className="text-xs text-slate-400">Click any module to expand video tutorials & docs</span>
        </div>

        <div className="flex flex-col gap-3">
          {roadmap.modules?.map((mod, i) => (
            <ModuleCard key={mod.title || i} mod={mod} index={i} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}