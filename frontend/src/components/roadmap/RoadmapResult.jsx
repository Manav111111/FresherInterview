import { motion } from "motion/react";
import { FiTarget, FiClock, FiCheckCircle, FiMap, FiX, FiArrowLeft } from "react-icons/fi";
import ModuleCard from "./ModuleCard";

export default function RoadmapResult({ roadmap, onClear }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header Card */}
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
              Target Compensation: <span className="text-indigo-600 font-bold">{roadmap.package}</span>
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

      {/* Modules List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <FiMap size={14} className="text-indigo-600" /> Learning Path Milestones
          </p>
          <span className="text-xs text-slate-400">Click any module to expand resources</span>
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