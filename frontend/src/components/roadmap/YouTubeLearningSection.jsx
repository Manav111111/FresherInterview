import React, { useState, useMemo } from "react";
import {
  FiPlay,
  FiExternalLink,
  FiCheck,
  FiX,
  FiSearch,
  FiInfo,
} from "react-icons/fi";
import { TechLogo } from "../../utils/logoResolver";

// Canonical visual themes and brand assets for top educators
const CREATOR_THEMES = {
  campusx: {
    bannerBg: "from-slate-900 via-neutral-900 to-slate-950",
    tagline: "Learn Today. Build Tomorrow.",
    accent: "border-sky-500",
    avatarBg: "bg-black text-white font-black",
    avatarText: "X",
  },
  krish_naik: {
    bannerBg: "from-slate-900 via-indigo-950 to-slate-900",
    tagline: "Data Science • ML • AI",
    accent: "border-indigo-500",
    avatarBg: "bg-indigo-700 text-white font-bold",
    avatarText: "KN",
  },
  codewithharry: {
    bannerBg: "from-neutral-900 via-stone-900 to-black",
    tagline: "Learn • Build • Grow",
    accent: "border-amber-500",
    avatarBg: "bg-stone-800 text-amber-400 font-bold",
    avatarText: "CWH",
  },
  apna_college: {
    bannerBg: "from-slate-900 via-blue-950 to-slate-900",
    tagline: "Code Your Career • Placement",
    accent: "border-blue-500",
    avatarBg: "bg-blue-600 text-white font-bold",
    avatarText: "AC",
  },
  chai_aur_code: {
    bannerBg: "from-stone-950 via-amber-950 to-neutral-950",
    tagline: "Code with Clarity & Depth",
    accent: "border-amber-600",
    avatarBg: "bg-amber-600 text-white font-bold",
    avatarText: "☕",
  },
  sheryians: {
    bannerBg: "from-neutral-950 via-red-950 to-black",
    tagline: "Dominating Modern Web Development",
    accent: "border-red-500",
    avatarBg: "bg-red-700 text-white font-bold",
    avatarText: "SCS",
  },
  thapa_technical: {
    bannerBg: "from-slate-900 via-cyan-950 to-slate-950",
    tagline: "Master Full Stack in Hindi",
    accent: "border-cyan-500",
    avatarBg: "bg-cyan-700 text-white font-bold",
    avatarText: "TT",
  },
  codebasics: {
    bannerBg: "from-slate-900 via-teal-950 to-slate-900",
    tagline: "Practical Data Science & Python",
    accent: "border-teal-500",
    avatarBg: "bg-teal-600 text-white font-bold",
    avatarText: "CB",
  },
  abhishek_veeramalla: {
    bannerBg: "from-slate-900 via-blue-950 to-slate-950",
    tagline: "DevOps & Cloud Zero to Hero",
    accent: "border-blue-500",
    avatarBg: "bg-blue-700 text-white font-bold",
    avatarText: "AV",
  },
  take_u_forward: {
    bannerBg: "from-neutral-900 via-purple-950 to-slate-950",
    tagline: "Take U Forward • A2Z DSA Sheet",
    accent: "border-purple-500",
    avatarBg: "bg-purple-700 text-white font-bold",
    avatarText: "TUF",
  },
  codehelp: {
    bannerBg: "from-slate-900 via-rose-950 to-slate-950",
    tagline: "Love Babbar DSA & Web Dev",
    accent: "border-rose-500",
    avatarBg: "bg-rose-600 text-white font-bold",
    avatarText: "CH",
  },
  kunal_kushwaha: {
    bannerBg: "from-slate-900 via-emerald-950 to-slate-900",
    tagline: "Java + DSA + Open Source",
    accent: "border-emerald-500",
    avatarBg: "bg-emerald-600 text-white font-bold",
    avatarText: "KK",
  },
  gaurav_sen: {
    bannerBg: "from-slate-900 via-indigo-950 to-black",
    tagline: "System Design & Distributed Systems",
    accent: "border-indigo-500",
    avatarBg: "bg-indigo-800 text-white font-bold",
    avatarText: "GS",
  },
  gate_smashers: {
    bannerBg: "from-slate-900 via-slate-800 to-slate-950",
    tagline: "Core CS, Networks & OS in Hindi",
    accent: "border-slate-500",
    avatarBg: "bg-slate-700 text-white font-bold",
    avatarText: "GS",
  },
};

export default function YouTubeLearningSection({ creators = [], allPlaylists = [] }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Normalize input data
  const featuredCreators = useMemo(() => {
    if (!Array.isArray(creators)) return [];
    // If creators is an array of grouped creator objects
    if (creators.length > 0 && creators[0]?.channel) {
      return creators.slice(0, 5);
    }
    // Fallback if flat list was provided
    if (creators.length > 0 && creators[0]?.title) {
      const grouped = {};
      for (const item of creators) {
        const cname = item.channel_name || "Curated Channel";
        const cid = item.logo_key || cname.toLowerCase().replace(/[^a-z0-9]/g, "_");
        if (!grouped[cid]) {
          grouped[cid] = {
            channel: {
              id: cid,
              name: cname,
              url: item.url,
              logo_key: item.logo_key || cid,
              subscribers: "Verified Channel",
              tags: [item.language || "Hindi", "Roadmap"],
            },
            playlists: [],
          };
        }
        if (grouped[cid].playlists.length < 3) {
          grouped[cid].playlists.push({
            title: item.title,
            url: item.url,
            language: item.language || "Hindi",
            video_count: item.video_count || "Series",
            verified: true,
          });
        }
      }
      return Object.values(grouped).slice(0, 5);
    }
    return [];
  }, [creators]);

  // Calculate dynamic playlist count
  const totalPlaylistsCount = useMemo(() => {
    return featuredCreators.reduce((acc, c) => acc + (c.playlists?.length || 0), 0);
  }, [featuredCreators]);

  // Filtered playlists for "View All" modal
  const modalCreators = useMemo(() => {
    if (!searchQuery.trim()) return creators;
    const q = searchQuery.toLowerCase();
    return creators.filter((c) => {
      const name = c.channel?.name?.toLowerCase() || "";
      const hasPl = c.playlists?.some((p) => p.title?.toLowerCase().includes(q));
      return name.includes(q) || hasPl;
    });
  }, [creators, searchQuery]);

  if (!featuredCreators || featuredCreators.length === 0) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 text-center shadow-xs">
        <p className="text-sm font-semibold text-slate-500">
          No curated playlists available yet for this roadmap.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── HEADER ── */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-start sm:items-center gap-3">
            {/* YouTube Red Icon Badge */}
            <div className="w-10 h-10 rounded-2xl bg-red-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-red-500/20">
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                Curated YouTube Learning Resources
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                High-quality, beginner-friendly playlists from trusted educators, tailored for your learning path.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto shrink-0">
            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-red-600 bg-red-50 border border-red-200/80 px-3 py-1 rounded-full shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />
              {featuredCreators.length} Featured YouTubers
            </span>

            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition flex items-center gap-1 hover:underline cursor-pointer"
            >
              <span>View All Channels</span>
              <span aria-hidden="true">&rarr;</span>
            </button>
          </div>
        </div>

        {/* ── 5 CREATOR CARDS GRID ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-5">
          {featuredCreators.map((item, idx) => {
            const ch = item.channel || {};
            const chId = ch.id || ch.logo_key || "generic";
            const theme = CREATOR_THEMES[chId] || {
              bannerBg: "from-slate-900 via-slate-800 to-slate-950",
              tagline: "Curated Masterclasses",
              accent: "border-slate-400",
              avatarBg: "bg-slate-800 text-white font-bold",
              avatarText: ch.name?.slice(0, 2)?.toUpperCase() || "YT",
            };

            const tags = ch.tags && ch.tags.length > 0
              ? ch.tags
              : ["Roadmap", "Tutorials", "Free"];

            const playlists = item.playlists || [];

            return (
              <div
                key={chId || idx}
                className="bg-white rounded-2xl border border-slate-200/90 hover:border-slate-300 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden group"
              >
                {/* 1. Header Banner */}
                <div>
                  <div
                    className={`bg-gradient-to-r ${theme.bannerBg} px-3.5 py-4 text-white relative overflow-hidden`}
                  >
                    <div className="relative z-10">
                      <p className="text-[11px] font-black tracking-wider uppercase text-white/90 truncate drop-shadow-xs">
                        {ch.name}
                      </p>
                      <p className="text-[9px] text-slate-300 font-medium tracking-tight truncate mt-0.5 opacity-90">
                        {theme.tagline}
                      </p>
                    </div>

                    {/* Subtle decorative glow */}
                    <div className="absolute -top-6 -right-6 w-20 h-20 bg-white/10 rounded-full blur-lg pointer-events-none" />
                  </div>

                  {/* 2. Avatar & Channel Info */}
                  <div className="p-3.5 pb-2">
                    <div className="flex items-center gap-2.5">
                      {/* Avatar Circle */}
                      <div
                        className={`w-10 h-10 rounded-full ${theme.avatarBg} flex items-center justify-center shrink-0 shadow-xs ring-2 ring-white text-xs tracking-wider`}
                      >
                        {theme.avatarText}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1 min-w-0">
                          <h4 className="text-xs font-bold text-slate-900 truncate">
                            {ch.name}
                          </h4>
                          {/* Verified Blue Badge */}
                          <span
                            className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-blue-500 text-white shrink-0"
                            title="Verified Educator"
                          >
                            <FiCheck size={9} strokeWidth={3} />
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-medium truncate">
                          {ch.subscribers || "Verified Educator"}
                        </p>
                      </div>
                    </div>

                    {/* 3. Topic Tags */}
                    <div className="flex flex-wrap gap-1 mt-3">
                      {tags.slice(0, 3).map((tag, tIdx) => (
                        <span
                          key={tIdx}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-blue-50/80 text-blue-700 border border-blue-100/80"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* 4. Recommended Playlists */}
                    <div className="mt-3.5">
                      <p className="text-[11px] font-bold text-slate-800 tracking-tight mb-2">
                        Recommended Playlists
                      </p>

                      <div className="space-y-1.5">
                        {playlists.map((pl, pIdx) => (
                          <a
                            key={pl.resource_id || pIdx}
                            href={pl.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group/item flex items-center justify-between gap-2 p-1.5 rounded-xl bg-slate-50/80 hover:bg-blue-50/80 border border-slate-100 hover:border-blue-200 transition"
                            title={`Watch: ${pl.title}`}
                          >
                            {/* Playlist thumbnail/icon */}
                            <div className="w-7 h-7 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0 group-hover/item:bg-blue-600 transition-colors">
                              <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                                <path d="M19 9H2v2h17V9zm0-4H2v2h17V5zM2 15h13v-2H2v2zm15-2v6l5-3-5-3z" />
                              </svg>
                            </div>

                            {/* Playlist title & meta */}
                            <div className="min-w-0 flex-1">
                              <p className="text-[11px] font-semibold text-slate-800 group-hover/item:text-blue-700 truncate leading-tight">
                                {pl.title}
                              </p>
                              <p className="text-[9px] text-slate-400 font-medium truncate mt-0.5">
                                {pl.video_count || (pl.language ? `${pl.language} playlist` : "Full series")}
                              </p>
                            </div>

                            {/* Small Play Button */}
                            <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 group-hover/item:bg-blue-600 group-hover/item:text-white flex items-center justify-center shrink-0 transition">
                              <FiPlay size={8} className="translate-x-[0.5px]" fill="currentColor" />
                            </div>
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 5. Visit Channel Button */}
                <div className="p-3 pt-0">
                  <a
                    href={ch.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full py-2 px-3 rounded-xl border border-red-100 bg-red-50/60 hover:bg-red-50 text-red-600 text-xs font-bold flex items-center justify-center gap-1.5 transition group/btn"
                  >
                    <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                    </svg>
                    <span>Visit Channel</span>
                    <FiExternalLink size={11} className="group-hover/btn:translate-x-0.5 transition-transform" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── BOTTOM BANNER TIP ── */}
        <div className="mt-5 rounded-2xl bg-indigo-50/50 border border-indigo-100/80 p-3.5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-indigo-900 font-medium">
            <span className="text-indigo-600 text-sm">✨</span>
            <span>
              These are handpicked, high-quality playlists to help you learn faster. All resources are verified and aligned with your roadmap.
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-600 shrink-0 font-medium">
            <span className="text-amber-500 text-sm">💡</span>
            <span>
              <strong className="text-slate-800">Tip:</strong> Start with the beginner playlists and follow the order suggested in your roadmap.
            </span>
          </div>
        </div>
      </div>

      {/* ── VIEW ALL CHANNELS MODAL DRAWER ── */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-red-600 text-white flex items-center justify-center">
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    All Curated Learning Resources
                  </h3>
                  <p className="text-xs text-slate-500">
                    Explore all verified educators and official learning playlists.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition"
              >
                <FiX size={16} />
              </button>
            </div>

            {/* Search Bar */}
            <div className="p-4 bg-slate-50/80 border-b border-slate-100">
              <div className="relative">
                <FiSearch size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by educator name or playlist topic (e.g., LangGraph, React, DSA)..."
                  className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4 flex-1">
              {modalCreators.length === 0 ? (
                <p className="text-center text-xs text-slate-400 py-10">
                  No matching playlists found.
                </p>
              ) : (
                modalCreators.map((item, idx) => {
                  const ch = item.channel || {};
                  return (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl border border-slate-200/80 bg-slate-50/40 hover:bg-white transition space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <h4 className="text-sm font-bold text-slate-900">
                            {ch.name}
                          </h4>
                          <span className="text-[10px] text-slate-500 font-medium">
                            {ch.subscribers}
                          </span>
                        </div>
                        <a
                          href={ch.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-bold text-red-600 hover:text-red-800 flex items-center gap-1"
                        >
                          <span>Visit Channel</span>
                          <FiExternalLink size={11} />
                        </a>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                        {(item.playlists || []).map((pl, pIdx) => (
                          <a
                            key={pIdx}
                            href={pl.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:border-blue-400 transition flex items-center justify-between gap-2 group"
                          >
                            <div className="min-w-0">
                              <p className="text-xs font-semibold text-slate-800 group-hover:text-blue-600 truncate">
                                {pl.title}
                              </p>
                              <p className="text-[10px] text-slate-400">
                                {pl.video_count || pl.language}
                              </p>
                            </div>
                            <FiPlay size={11} className="text-blue-600 shrink-0" fill="currentColor" />
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-100 bg-slate-50/60 flex justify-end">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
