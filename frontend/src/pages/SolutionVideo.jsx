import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiPlay,
  FiVideo,
  FiArrowRight,
  FiRotateCcw,
  FiEdit3,
  FiHelpCircle,
  FiCheckCircle,
  FiAlertCircle,
  FiChevronDown,
  FiChevronUp,
} from "react-icons/fi";
import { BsStars } from "react-icons/bs";

import Sidebar from "../components/Sidebar";
import WhiteboardCanvas from "../components/video-solution/WhiteboardCanvas";
import VideoPlayerControls from "../components/video-solution/VideoPlayerControls";
import VideoProgressTracker from "../components/video-solution/VideoProgressTracker";
import { AudioNarrationEngine } from "../components/video-solution/AudioNarrationEngine";
import { VideoRecorder } from "../components/video-solution/VideoRecorder";
import { generateSolutionVideo } from "../api/video.api";
import { logoutUser } from "../api/user.api";
import { useNavigate } from "react-router-dom";

const EXAMPLE_QUESTIONS = [
  { label: "📐 Linear Equation", text: "Solve 2x + 5 = 15" },
  { label: "⚡ Binary Search", text: "How does the Binary Search algorithm work?" },
  { label: "🍎 Newton's 2nd Law", text: "Explain Newton's Second Law of Motion: F = ma" },
  { label: "🧮 Calculus Derivative", text: "Find the derivative of f(x) = x^3 + 4x - 7" },
  { label: "🌱 Photosynthesis", text: "How does the process of photosynthesis work in plants?" },
];

export default function SolutionVideo({ user, setUser }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  // Feature States
  const [questionInput, setQuestionInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Video Solution State
  const [videoData, setVideoData] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);

  // References
  const canvasRef = useRef(null);
  const videoContainerRef = useRef(null);
  const audioRef = useRef(new AudioNarrationEngine());
  const animationFrameRef = useRef(null);
  const lastTimeRef = useRef(null);

  const totalDuration = videoData?.totalDuration || 16.0;
  const scenes = videoData?.scenes || [];

  const handleLogout = async () => {
    try {
      await logoutUser();
      setUser(null);
      navigate("/");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  // Find active scene based on current time
  const getActiveScene = useCallback(
    (time) => {
      let accumulated = 0;
      for (const scene of scenes) {
        const dur = scene.duration || 3.5;
        if (time >= accumulated && time < accumulated + dur) {
          return scene;
        }
        accumulated += dur;
      }
      return scenes[scenes.length - 1] || null;
    },
    [scenes]
  );

  // Animation playback loop
  useEffect(() => {
    if (!isPlaying || !videoData) {
      lastTimeRef.current = null;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    const step = (timestamp) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp;
      const delta = (timestamp - lastTimeRef.current) / 1000;
      lastTimeRef.current = timestamp;

      setCurrentTime((prevTime) => {
        const nextTime = prevTime + delta;
        if (nextTime >= totalDuration) {
          setIsPlaying(false);
          audioRef.current.stop();
          return totalDuration;
        }

        // Trigger synchronized voice narration for active scene
        const activeScene = getActiveScene(nextTime);
        if (activeScene) {
          audioRef.current.speakScene(activeScene);
        }

        return nextTime;
      });

      animationFrameRef.current = requestAnimationFrame(step);
    };

    animationFrameRef.current = requestAnimationFrame(step);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, videoData, totalDuration, getActiveScene]);

  // Handle Play / Pause
  const handlePlayPause = () => {
    if (currentTime >= totalDuration) {
      setCurrentTime(0);
      audioRef.current.reset();
    }
    setIsPlaying(!isPlaying);
  };

  // Handle Seek / Scrub
  const handleSeek = (newTime) => {
    setCurrentTime(newTime);
    const activeScene = getActiveScene(newTime);
    if (isPlaying && activeScene) {
      audioRef.current.speakScene(activeScene);
    } else {
      audioRef.current.stop();
    }
  };

  // Handle Replay
  const handleReplay = () => {
    audioRef.current.reset();
    setCurrentTime(0);
    setIsPlaying(true);
  };

  // Handle Mute Toggle
  const handleToggleMute = () => {
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    audioRef.current.setMuted(nextMute);
  };

  // Handle Fullscreen
  const handleToggleFullscreen = () => {
    if (!videoContainerRef.current) return;
    if (!document.fullscreenElement) {
      videoContainerRef.current.requestFullscreen?.().catch((err) => {
        console.warn("Fullscreen request error:", err);
      });
    } else {
      document.exitFullscreen?.();
    }
  };

  // Handle Video Generation Submission
  const handleGenerate = async (questionToSubmit) => {
    const q = (questionToSubmit || questionInput).trim();
    if (!q) {
      setErrorMsg("Please enter a question or problem to explain.");
      return;
    }

    setErrorMsg("");
    setIsGenerating(true);
    setIsPlaying(false);
    setCurrentTime(0);
    audioRef.current.stop();

    try {
      const res = await generateSolutionVideo(q);
      if (res?.data) {
        setVideoData(res.data);
        setCurrentTime(0);
        setTimeout(() => {
          setIsPlaying(true);
        }, 500);
      } else {
        throw new Error("Invalid response format from server.");
      }
    } catch (err) {
      console.error("Failed to generate video:", err);
      setErrorMsg(
        err.response?.data?.detail ||
          "Failed to generate video solution. Please check your question and try again."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle Real WebM Video Download
  const handleDownloadVideo = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (!VideoRecorder.isSupported()) {
      alert("Video recording is not supported in this browser.");
      return;
    }

    setIsRecording(true);
    setIsPlaying(false);
    setCurrentTime(0);
    audioRef.current.stop();

    const recorder = new VideoRecorder(canvas);
    try {
      recorder.start();

      // Play through the video at normal speed while recording
      setIsPlaying(true);

      const checkInterval = setInterval(async () => {
        if (currentTime >= totalDuration) {
          clearInterval(checkInterval);
          setIsPlaying(false);
          const result = await recorder.stop();
          if (result?.blob) {
            const cleanTitle = (videoData?.question || "solution")
              .toLowerCase()
              .replace(/[^a-z0-9]/g, "-")
              .slice(0, 30);
            recorder.downloadBlob(result.blob, `solution-${cleanTitle}.${result.extension}`);
          }
          setIsRecording(false);
        }
      }, 200);
    } catch (err) {
      console.error("Recording failed:", err);
      setIsRecording(false);
      alert("Recording failed: " + err.message);
    }
  };

  return (
    <div className="bg-[#F8F9FA] min-h-screen text-[#0A0A0A] font-sans flex">
      {/* App Sidebar Navigation */}
      <Sidebar
        user={user}
        onNewInterview={() => navigate("/interview")}
        onLogout={handleLogout}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content */}
      <motion.main
        className={`flex-1 min-h-screen px-3 sm:px-6 md:px-8 py-5 md:py-7 transition-all duration-300 ${
          collapsed ? "md:ml-[72px]" : "md:ml-[260px]"
        }`}
      >
        {/* Header Bar */}
        <div className="max-w-4xl mx-auto mb-6">
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-600 mb-1">
            <BsStars size={14} />
            <span>AI Educational Studio</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0A0A0A] tracking-tight">
            AI Solution Video Generator
          </h1>
          <p className="text-xs sm:text-sm text-black/50 mt-1">
            Turn any question into a clear, animated whiteboard explanation video with voice narration in seconds.
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="max-w-4xl mx-auto mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-700 text-xs flex items-center gap-3">
            <FiAlertCircle size={16} className="shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Input Card Mode */}
        {!videoData && !isGenerating && (
          <div className="max-w-4xl mx-auto bg-white rounded-2xl border border-black/8 p-5 sm:p-7 shadow-sm">
            <label className="block text-xs font-bold uppercase tracking-wider text-black/60 mb-2">
              Enter Your Question or Problem Statement
            </label>

            <div className="relative">
              <textarea
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    handleGenerate();
                  }
                }}
                placeholder="e.g., Solve 2x + 5 = 15, or Explain how Binary Search works..."
                rows={4}
                className="w-full rounded-xl border border-black/15 bg-black/[0.01] p-4 text-sm text-[#0A0A0A] placeholder-black/30 focus:border-purple-500 focus:bg-white focus:outline-none transition resize-none"
              />
              <div className="absolute bottom-3 right-3 text-[10px] text-black/40">
                Press <kbd className="px-1.5 py-0.5 rounded bg-black/5 font-mono">Ctrl+Enter</kbd> to generate
              </div>
            </div>

            {/* Quick Example Chips */}
            <div className="mt-4">
              <span className="text-[11px] font-semibold text-black/45 block mb-2">
                Try one of these examples:
              </span>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUESTIONS.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuestionInput(item.text);
                      handleGenerate(item.text);
                    }}
                    className="px-3 py-1.5 rounded-lg border border-black/10 bg-black/[0.02] hover:bg-purple-50 hover:border-purple-300 text-xs text-black/70 hover:text-purple-700 transition"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Action Button */}
            <div className="mt-6 flex items-center justify-end">
              <button
                onClick={() => handleGenerate()}
                disabled={!questionInput.trim() || isGenerating}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#000000] text-white text-xs font-semibold hover:bg-[#1a1a1a] transition shadow-md disabled:opacity-40"
              >
                <FiVideo size={14} />
                <span>Generate Solution Video</span>
                <FiArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Asynchronous Progress Tracker */}
        {isGenerating && <VideoProgressTracker isGenerating={isGenerating} />}

        {/* Video Player & Interactive Solution View */}
        {videoData && !isGenerating && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Top Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 px-4 rounded-xl border border-black/8">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-black/80">Topic:</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 font-semibold border border-purple-200">
                  {videoData.topic}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setVideoData(null);
                    setQuestionInput("");
                    audioRef.current.stop();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-black/15 text-xs text-black/70 hover:border-black/30 hover:text-black transition"
                >
                  <FiEdit3 size={13} />
                  <span>New Question</span>
                </button>

                <button
                  onClick={() => handleGenerate(videoData.question)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black text-white text-xs font-medium hover:bg-black/80 transition"
                >
                  <FiRotateCcw size={13} />
                  <span>Regenerate</span>
                </button>
              </div>
            </div>

            {/* Video Player Container */}
            <div ref={videoContainerRef} className="space-y-4">
              <WhiteboardCanvas
                question={videoData.question}
                topic={videoData.topic}
                scenes={videoData.scenes}
                currentTime={currentTime}
                totalDuration={totalDuration}
                canvasRef={canvasRef}
              />

              <VideoPlayerControls
                isPlaying={isPlaying}
                currentTime={currentTime}
                totalDuration={totalDuration}
                isMuted={isMuted}
                isRecording={isRecording}
                onPlayPause={handlePlayPause}
                onSeek={handleSeek}
                onReplay={handleReplay}
                onToggleMute={handleToggleMute}
                onToggleFullscreen={handleToggleFullscreen}
                onDownloadVideo={handleDownloadVideo}
              />
            </div>

            {/* Step-by-Step Breakdown Accordion */}
            <div className="bg-white rounded-2xl border border-black/8 overflow-hidden shadow-sm">
              <button
                onClick={() => setShowTranscript(!showTranscript)}
                className="w-full flex items-center justify-between p-4 px-5 text-left border-b border-black/5 hover:bg-black/[0.01] transition"
              >
                <div className="flex items-center gap-2">
                  <FiCheckCircle className="text-emerald-500" size={16} />
                  <span className="text-xs font-bold text-black uppercase tracking-wider">
                    Step-by-Step Explanation Transcript ({scenes.length} Steps)
                  </span>
                </div>
                {showTranscript ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
              </button>

              <AnimatePresence>
                {showTranscript && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="p-5 space-y-4"
                  >
                    {scenes.map((scene, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border transition ${
                          scene.isFinal
                            ? "bg-emerald-50/60 border-emerald-200"
                            : "bg-black/[0.02] border-black/5"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className={`text-[11px] font-bold uppercase tracking-wider ${
                              scene.isFinal ? "text-emerald-700" : "text-purple-600"
                            }`}
                          >
                            {scene.isFinal ? "Final Result" : `Step ${scene.step || idx + 1}: ${scene.title}`}
                          </span>
                          <span className="text-[10px] text-black/40 font-mono">
                            {scene.duration}s
                          </span>
                        </div>

                        <div className="font-mono text-sm font-semibold text-black/90 mb-1">
                          {scene.content}
                        </div>

                        <p className="text-xs text-black/60 italic">
                          "{scene.narration}"
                        </p>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}
      </motion.main>
    </div>
  );
}
