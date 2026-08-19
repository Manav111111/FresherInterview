import React, { useEffect, useState } from "react";
import { motion } from "motion/react";
import { FiCheck, FiCpu, FiEdit3, FiLayers, FiVolume2, FiVideo } from "react-icons/fi";

const STAGES = [
  { id: 1, label: "Analyzing Question & Problem Statement", icon: FiCpu },
  { id: 2, label: "Generating Step-by-Step Educational Solution", icon: FiEdit3 },
  { id: 3, label: "Planning Scene Timelines & Handwriting Paths", icon: FiLayers },
  { id: 4, label: "Preparing Voice Narration & Audio Synchronization", icon: FiVolume2 },
  { id: 5, label: "Rendering Interactive Whiteboard Video", icon: FiVideo },
];

export default function VideoProgressTracker({ isGenerating }) {
  const [currentStage, setCurrentStage] = useState(1);

  useEffect(() => {
    if (!isGenerating) {
      setCurrentStage(1);
      return;
    }

    // Step through the visual progression smoothly
    const t1 = setTimeout(() => setCurrentStage(2), 800);
    const t2 = setTimeout(() => setCurrentStage(3), 2000);
    const t3 = setTimeout(() => setCurrentStage(4), 3600);
    const t4 = setTimeout(() => setCurrentStage(5), 5200);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [isGenerating]);

  if (!isGenerating) return null;

  return (
    <div className="w-full max-w-xl mx-auto bg-[#0E121B] border border-white/15 rounded-2xl p-6 shadow-2xl text-white my-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Generating AI Solution Video</h3>
          <p className="text-xs text-white/50">Creating synchronized whiteboard animation & voice narration...</p>
        </div>
      </div>

      {/* Stepper */}
      <div className="space-y-3.5">
        {STAGES.map((stage) => {
          const Icon = stage.icon;
          const isDone = currentStage > stage.id;
          const isCurrent = currentStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl border transition-all ${
                isDone
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : isCurrent
                  ? "bg-purple-500/15 border-purple-500/40 text-purple-200 shadow-sm"
                  : "bg-white/[0.02] border-white/5 text-white/30"
              }`}
            >
              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                  isDone
                    ? "bg-emerald-500 text-black"
                    : isCurrent
                    ? "bg-purple-500 text-white animate-pulse"
                    : "bg-white/10 text-white/40"
                }`}
              >
                {isDone ? <FiCheck size={13} /> : <Icon size={13} />}
              </div>

              <span className="text-xs font-medium">{stage.label}</span>

              {isCurrent && (
                <span className="ml-auto text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-500/30 text-purple-200 animate-pulse">
                  Processing
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
