/**
 * YouTubeLearningSection — Curated Channel Cards
 *
 * Rules (enforced by design):
 * - Renders channel-level objects only. No playlists.
 * - Does NOT infer logos. Uses YouTube's /vi/ thumbnail API with a text-avatar fallback.
 * - Does NOT show fake verification badges.
 * - Does NOT show subscriber counts (we have no live API source).
 * - Every link comes directly from the backend channel_registry.
 */

import React, { useState } from "react";
import { FiExternalLink, FiYoutube } from "react-icons/fi";

// ─── YouTube Channel Avatar ──────────────────────────────────────────────────
// We don't have direct access to YouTube channel thumbnails without the API,
// so we use a clean text avatar with the registry-supplied colour and initials.
// If YouTube ever provides an unauthenticated thumbnail endpoint for channels,
// replace this with an <img> using that URL.

function ChannelAvatar({ initials, color, size = 48 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        minWidth: size,
        background: color || "#374151",
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 800,
        fontSize: Math.round(size * 0.33),
        color: "#fff",
        letterSpacing: "-0.02em",
        userSelect: "none",
      }}
      aria-hidden="true"
    >
      {(initials || "YT").slice(0, 3)}
    </div>
  );
}

// ─── Single Channel Card ──────────────────────────────────────────────────────

function ChannelCard({ channel }) {
  const {
    name,
    channel_url,
    avatar_initials,
    avatar_color,
    topics = [],
    best_for,
  } = channel;

  return (
    <div
      className="group flex flex-col bg-white rounded-2xl border border-slate-200/80 hover:border-red-300 hover:shadow-md transition-all duration-200 overflow-hidden"
      style={{ boxShadow: "0 1px 3px 0 rgba(0,0,0,0.04)" }}
    >
      {/* Card Body */}
      <div className="flex items-start gap-3.5 p-4 flex-1">
        {/* Avatar */}
        <div className="shrink-0 mt-0.5">
          <ChannelAvatar
            initials={avatar_initials}
            color={avatar_color}
            size={44}
          />
        </div>

        {/* Channel Info */}
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-bold text-slate-900 truncate group-hover:text-red-600 transition-colors leading-tight">
            {name}
          </h4>

          {/* Topic pills */}
          {topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {topics.slice(0, 4).map((topic, i) => (
                <span
                  key={i}
                  className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600"
                >
                  {topic}
                </span>
              ))}
            </div>
          )}

          {/* Best For */}
          {best_for && (
            <p className="text-[11px] text-slate-500 mt-1.5 leading-snug line-clamp-2">
              {best_for}
            </p>
          )}
        </div>
      </div>

      {/* Footer CTA */}
      {channel_url && (
        <div className="border-t border-slate-100 px-4 py-2.5">
          <a
            href={channel_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-red-600 hover:text-red-700 transition-colors"
            title={`Visit ${name} on YouTube`}
          >
            <FiYoutube size={13} />
            <span>Visit Channel</span>
            <FiExternalLink size={10} />
          </a>
        </div>
      )}
    </div>
  );
}

// ─── Section Container ────────────────────────────────────────────────────────

export default function YouTubeLearningSection({ creators = [] }) {
  // Normalise: backend now sends flat channel objects; also handle legacy format
  const channels = creators.map((item) => {
    // New flat format
    if (item.channel_id || item.avatar_initials) return item;
    // Legacy {channel:{…}, playlists:[…]} format — extract channel data
    if (item.channel) {
      const ch = item.channel;
      return {
        channel_id: ch.id || ch.channel_id || "",
        name: ch.name || "YouTube Channel",
        channel_url: ch.url || ch.channel_url || "",
        avatar_initials: (ch.name || "YT").slice(0, 2).toUpperCase(),
        avatar_color: "#DC2626",
        topics: ch.tags || [],
        best_for: ch.best_for || "",
      };
    }
    // Flat yt_items fallback
    return {
      channel_id: "",
      name: item.channel_name || item.name || "YouTube Channel",
      channel_url: item.url || item.channel_url || "",
      avatar_initials: (item.channel_name || item.name || "YT").slice(0, 2).toUpperCase(),
      avatar_color: "#DC2626",
      topics: item.topics || [],
      best_for: item.best_for || "",
    };
  }).filter((ch) => ch.name && ch.channel_url);

  if (channels.length === 0) return null;

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-red-50 text-red-600 flex items-center justify-center">
            <FiYoutube size={15} />
          </div>
          <h3 className="text-base font-bold text-slate-900">
            Curated YouTube Channels
          </h3>
        </div>
        <span className="text-[11px] font-bold text-red-700 bg-red-50 border border-red-200 px-3 py-0.5 rounded-full">
          {channels.length} Channels
        </span>
      </div>

      {/* Channel Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {channels.map((ch, idx) => (
          <ChannelCard key={ch.channel_id || idx} channel={ch} />
        ))}
      </div>

      {/* Footer note */}
      <p className="text-[10px] text-slate-400 text-right pt-1">
        Channels selected based on your target role and skill gaps.
      </p>
    </div>
  );
}
