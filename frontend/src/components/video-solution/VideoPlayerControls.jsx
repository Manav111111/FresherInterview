import React from "react";
import {
  FiPlay,
  FiPause,
  FiRotateCcw,
  FiVolume2,
  FiVolumeX,
  FiMaximize2,
  FiDownload,
  FiCheck,
} from "react-icons/fi";

/**
 * Formats seconds into MM:SS format
 */
const formatTime = (seconds) => {
  const s = Math.max(0, Math.floor(seconds || 0));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
};

export default function VideoPlayerControls({
  isPlaying,
  currentTime,
  totalDuration,
  isMuted,
  isRecording,
  recordingProgress,
  onPlayPause,
  onSeek,
  onReplay,
  onToggleMute,
  onToggleFullscreen,
  onDownloadVideo,
}) {
  const progressPct = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

  return (
    <div className="w-full bg-[#0A0D14] border border-white/10 rounded-2xl p-3 sm:p-4 text-white shadow-xl space-y-3">
      {/* Seekable Progress Bar */}
      <div className="relative flex items-center group cursor-pointer">
        <input
          type="range"
          min={0}
          max={totalDuration || 1}
          step={0.05}
          value={currentTime || 0}
          onChange={(e) => onSeek(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-white/20 rounded-lg appearance-none cursor-pointer accent-purple-500 hover:h-2 transition-all"
        />
      </div>

      {/* Control Buttons & Timestamps */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Playback Controls */}
        <div className="flex items-center gap-2">
          {/* Play / Pause */}
          <button
            onClick={onPlayPause}
            className="w-10 h-10 rounded-xl bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center transition shadow-lg shadow-purple-600/30"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <FiPause size={18} /> : <FiPlay size={18} className="ml-0.5" />}
          </button>

          {/* Replay */}
          <button
            onClick={onReplay}
            className="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 text-white/80 hover:text-white flex items-center justify-center transition"
            title="Replay Video"
          >
            <FiRotateCcw size={16} />
          </button>

          {/* Volume Mute Toggle */}
          <button
            onClick={onToggleMute}
            className="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 text-white/80 hover:text-white flex items-center justify-center transition"
            title={isMuted ? "Unmute Voice Narration" : "Mute Voice Narration"}
          >
            {isMuted ? <FiVolumeX size={16} className="text-red-400" /> : <FiVolume2 size={16} />}
          </button>

          {/* Time Display */}
          <div className="text-xs font-mono text-white/60 ml-2">
            <span className="text-white font-semibold">{formatTime(currentTime)}</span>
            {" / "}
            <span>{formatTime(totalDuration)}</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Download WebM Video Button */}
          <button
            onClick={onDownloadVideo}
            disabled={isRecording}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white text-black font-semibold text-xs hover:bg-white/90 transition shadow-md disabled:opacity-50"
            title="Download Video File (WebM)"
          >
            {isRecording ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                <span>Recording...</span>
              </>
            ) : (
              <>
                <FiDownload size={14} />
                <span>Download Video (.webm)</span>
              </>
            )}
          </button>

          {/* Fullscreen Button */}
          <button
            onClick={onToggleFullscreen}
            className="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 text-white/80 hover:text-white flex items-center justify-center transition hidden sm:flex"
            title="Fullscreen"
          >
            <FiMaximize2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
