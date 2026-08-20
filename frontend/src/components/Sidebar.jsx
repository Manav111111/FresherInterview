import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiHome,
  FiCpu,
  FiBarChart2,
  FiFileText,
  FiMap,
  FiVideo,
  FiLogOut,
  FiSidebar,
  FiChevronRight,
  FiArrowUpRight,
} from "react-icons/fi";
import { GiArtificialHive } from "react-icons/gi";
import { BsStars } from "react-icons/bs";

import { useNavigate, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  {
    icon: <FiHome size={17} />,
    label: "Home",
    path: "/dashboard",
  },
  {
    icon: <FiCpu size={17} />,
    label: "Practice",
    path: "/interview",
  },
  {
    icon: <FiBarChart2 size={17} />,
    label: "Performance",
    path: "/performance",
  },
  {
    icon: <FiFileText size={17} />,
    label: "Resume",
    path: "/resume",
  },
  {
    icon: <FiMap size={17} />,
    label: "Roadmap",
    path: "/roadmap",
  },
  {
    icon: <FiVideo size={17} />,
    label: "Solution Videos",
    path: "/solution-video",
  },
];

export default function Sidebar({
  user,
  onNewInterview,
  onLogout,
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "FC";

  const inner = (
    <div className="flex flex-col h-full bg-[#FFFFFF] text-slate-800 select-none">
      {/* ── Brand Logo Header ── */}
      <div
        className={`px-4 h-[64px] border-b border-slate-100 shrink-0 flex items-center ${
          collapsed ? "justify-center" : "justify-between"
        }`}
      >
        <div
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <GiArtificialHive size={20} color="white" />
          </div>

          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -6 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-1.5"
            >
              <span className="font-extrabold text-base tracking-tight text-slate-900">
                Fresher.Ai
              </span>
            </motion.div>
          )}
        </div>

        <div className="flex items-center gap-1">
          {/* Desktop Toggle Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors shrink-0"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <FiSidebar size={16} />
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors shrink-0"
          >
            <FiSidebar size={16} />
          </button>
        </div>
      </div>

      {/* ── Main Navigation Items ── */}
      <div className="px-3 py-4 flex-1 overflow-y-auto space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path === "/dashboard" && location.pathname === "/");

          return (
            <motion.button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
              whileHover={{ x: collapsed ? 0 : 2 }}
              transition={{ duration: 0.12 }}
              className={`w-full flex items-center gap-3 rounded-xl py-2.5 transition-all text-xs font-semibold ${
                collapsed ? "justify-center px-0" : "px-3.5"
              } ${
                isActive
                  ? "bg-[#EEF2FF] text-[#4F46E5] shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <span
                className={`shrink-0 transition-colors ${
                  isActive ? "text-[#4F46E5]" : "text-slate-400 group-hover:text-slate-600"
                }`}
              >
                {item.icon}
              </span>

              {!collapsed && (
                <span className="whitespace-nowrap text-[13px] tracking-tight font-medium">
                  {item.label}
                </span>
              )}
            </motion.button>
          );
        })}
      </div>

      {/* ── Bottom Section (Credits Card + User Profile) ── */}
      <div className="p-3 shrink-0 space-y-2.5 border-t border-slate-100">
        {/* Upgrade / Credits Card */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative rounded-2xl bg-gradient-to-br from-[#FFF7ED] via-[#FFF5ED] to-[#FFEDD5]/60 border border-orange-200/60 p-3.5 shadow-xs overflow-hidden"
            >
              <div className="absolute top-2 right-2.5 text-orange-300 opacity-60">
                <BsStars size={16} />
              </div>

              <div className="relative z-10">
                <div className="flex items-center gap-1.5 mb-1">
                  <h4 className="text-xs font-bold text-slate-800 tracking-tight">
                    Upgrade Your Preparation
                  </h4>
                </div>

                <p className="text-[11px] text-slate-500 leading-relaxed mb-3">
                  Unlock advanced AI features and personalised insights.
                </p>

                <div className="flex items-center justify-between gap-2">
                  <button
                    onClick={() => {
                      navigate("/pricing");
                      setMobileOpen(false);
                    }}
                    className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white text-xs font-semibold shadow-xs transition-all hover:scale-[1.02] active:scale-[0.98]"
                  >
                    <span>Explore Pro</span>
                    <FiArrowUpRight size={13} />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* User Profile Row */}
        <div className="relative">
          <div
            onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
            className={`flex items-center gap-2.5 p-2 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer ${
              collapsed ? "justify-center" : ""
            }`}
          >
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt={user.name}
                className="w-8 h-8 rounded-full object-cover shrink-0 border border-slate-200"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center shrink-0 shadow-xs">
                <span className="text-white font-bold text-xs">{initials}</span>
              </div>
            )}

            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-slate-900 text-xs font-bold truncate">
                  {user?.name ?? "Fresher Candidate"}
                </p>
                <p className="text-slate-400 text-[10px] truncate">
                  {user?.email ?? "candidate@fresherai.com"}
                </p>
              </div>
            )}

            {!collapsed && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onLogout?.();
                }}
                className="text-slate-400 hover:text-red-600 p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                title="Logout"
              >
                <FiLogOut size={13} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* ── DESKTOP sidebar ── */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ duration: 0.22, ease: "easeInOut" }}
        className="hidden md:flex fixed top-0 left-0 h-screen bg-white border-r border-slate-100 flex-col z-40 overflow-hidden shadow-xs"
      >
        {inner}
      </motion.aside>

      {/* ── MOBILE backdrop ── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 bg-slate-900/30 z-40 md:hidden backdrop-blur-xs"
          />
        )}
      </AnimatePresence>

      {/* ── MOBILE drawer ── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="fixed top-0 left-0 h-screen w-[260px] max-w-[85vw] bg-white border-r border-slate-100 flex flex-col z-50 md:hidden overflow-hidden shadow-2xl"
          >
            {inner}
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}