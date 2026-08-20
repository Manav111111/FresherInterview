import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiClock, FiChevronDown, FiChevronUp,
  FiYoutube, FiBookOpen, FiCheckCircle
} from "react-icons/fi";

const difficultyColor = {
  Easy: "text-emerald-700 bg-emerald-50 border-emerald-200",
  Medium: "text-purple-700 bg-purple-50 border-purple-200",
  Hard: "text-rose-700 bg-rose-50 border-rose-200",
};

const statusStyle = {
  Completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  "In Progress": "bg-indigo-50 text-indigo-700 border-indigo-200",
  Pending: "bg-slate-100 text-slate-600 border-slate-200",
};

export default function ModuleCard({ mod, index }) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      whileHover={{ y: -1 }}
      onClick={() => setOpen(!open)}
      className="bg-white border border-slate-200/80 rounded-2xl cursor-pointer select-none shadow-xs hover:border-indigo-300 transition-all overflow-hidden"
    >
      <div className="flex items-center gap-3.5 p-4 sm:p-5">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold bg-indigo-50 text-indigo-600 border border-indigo-100 shrink-0">
          {index + 1}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm font-bold text-slate-900 truncate">
            {mod.title}
          </p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <FiClock size={11} className="text-slate-400" />
            <span className="text-[11px] text-slate-500 font-medium">{mod.duration || "1-2 Weeks"}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${statusStyle[mod.status] || statusStyle.Pending}`}>
            {mod.status || "Planned"}
          </span>
          <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border hidden sm:inline-block ${difficultyColor[mod.difficulty] || difficultyColor.Medium}`}>
            {mod.difficulty || "Intermediate"}
          </span>
          <div className="p-1 text-slate-400">
            {open ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 pt-1 border-t border-slate-100 bg-slate-50/50 space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed mt-2">
                {mod.description || "Master core concepts and hands-on practice for this milestone."}
              </p>

              <div className="flex gap-2.5 flex-wrap pt-1">
                {mod.youtube && (
                  <a
                    href={mod.youtube}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 transition cursor-pointer"
                    >
                      <FiYoutube size={13} /> Watch Video Guide
                    </button>
                  </a>
                )}
                {mod.article && (
                  <a
                    href={mod.article}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 transition cursor-pointer"
                    >
                      <FiBookOpen size={13} /> Documentation
                    </button>
                  </a>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}