import React from "react";
import { GiArtificialHive } from "react-icons/gi";

export default function BrandedLoading({ message = "Loading Fresher.AI..." }) {
  return (
    <div className="min-h-screen bg-[#F8F9FB] flex flex-col items-center justify-center p-6 text-slate-800 selection:bg-indigo-100">
      {/* Centered Branded Card */}
      <div className="relative flex flex-col items-center max-w-sm w-full p-8 rounded-3xl bg-white/90 backdrop-blur-xl border border-indigo-50 shadow-[0_8px_32px_rgba(79,70,229,0.08)]">
        {/* Animated Glow Halo */}
        <div className="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-pink-500/10 blur-xl opacity-60 animate-pulse pointer-events-none" />

        {/* Logo Badge */}
        <div className="relative z-10 w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-5 animate-bounce">
          <GiArtificialHive size={34} color="white" />
        </div>

        {/* Brand Name */}
        <h2 className="relative z-10 text-xl font-extrabold text-slate-900 tracking-tight">
          Fresher<span className="text-indigo-600">.Ai</span>
        </h2>

        {/* Subtext */}
        <p className="relative z-10 text-xs text-slate-500 font-medium mt-1 text-center">
          {message}
        </p>

        {/* Progress bar shimmer */}
        <div className="relative z-10 w-44 h-1.5 bg-slate-100 rounded-full mt-6 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full animate-indeterminate" />
        </div>
      </div>
    </div>
  );
}
