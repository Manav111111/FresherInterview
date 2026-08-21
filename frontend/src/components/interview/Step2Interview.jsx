import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiArrowRight,
  FiClock,
  FiMessageSquare,
  FiMic,
  FiMicOff,
  FiCamera,
  FiCameraOff,
  FiCode,
  FiSquare,
  FiPause,
  FiPlay,
  FiRotateCcw,
  FiZap,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import Timer from "./Timer";
import maleVideo from "../../assets/male-ai.mp4";
import femaleVideo from "../../assets/female-ai.mp4";
import CodeEditorPanel from "./CodeEditorPanel";
import { submitAnswer, transcribeAudio } from "../../api/interview.api";
import { createAudioRecorder } from "../../services/audioRecorder";

function Step2Interview({ interviewData, user }) {
  const navigate = useNavigate();

  // ── State ──
  const [question, setQuestion] = useState(interviewData.question);
  const [currentIndex, setCurrentIndex] = useState(interviewData.currentQuestion || 0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(interviewData.question?.timer || 60);
  const [timerActive, setTimerActive] = useState(true);

  // UI toggles
  const [cameraOn, setCameraOn] = useState(false);
  const [codeOpen, setCodeOpen] = useState(false);

  // Advanced Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState(0);

  // Speech Output
  const [isAIPlaying, setIsAIPlaying] = useState(false);
  const [subtitle, setSubtitle] = useState("");
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [voiceGender, setVoiceGender] = useState("female");
  const [introSpoken, setIntroSpoken] = useState(false);

  // Refs
  const aiVideoRef = useRef(null);
  const userVideoRef = useRef(null);
  const streamRef = useRef(null);
  const audioRecorderRef = useRef(null);
  const animFrameRef = useRef(null);
  const recognitionRef = useRef(null);

  const videoSource = voiceGender === "male" ? maleVideo : femaleVideo;
  const userName = user?.name || "Candidate";
  const userInitial = userName.charAt(0).toUpperCase();
  const totalQuestions = interviewData.totalQuestions || 5;
  const progress = ((currentIndex + 1) / totalQuestions) * 100;

  // ── Initialize Audio Recorder instance ──
  useEffect(() => {
    audioRecorderRef.current = createAudioRecorder();
    return () => {
      audioRecorderRef.current?.cleanup();
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  // ── Load voices for Web Speech Synthesis ──
  useEffect(() => {
    const load = () => {
      const voices = window.speechSynthesis.getVoices();
      if (!voices.length) return;
      const female = voices.find((v) => /zira|samantha|female|google uk english female/i.test(v.name));
      const male = voices.find((v) => /david|mark|male|google uk english male/i.test(v.name));
      if (female) {
        setSelectedVoice(female);
        setVoiceGender("female");
      } else if (male) {
        setSelectedVoice(male);
        setVoiceGender("male");
      } else {
        setSelectedVoice(voices[0]);
        setVoiceGender("female");
      }
    };
    load();
    window.speechSynthesis.onvoiceschanged = load;
  }, []);

  const browserSpeechTextRef = useRef("");

  // ── Client-side live speech recognition fallback ──
  useEffect(() => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;
    try {
      const rec = new SpeechRec();
      rec.lang = "en-US";
      rec.continuous = true;
      rec.interimResults = true;
      rec.onresult = (e) => {
        let text = "";
        for (let i = 0; i < e.results.length; i++) {
          text += e.results[i][0].transcript + " ";
        }
        browserSpeechTextRef.current = text.trim();
      };
      recognitionRef.current = rec;
    } catch (_) {}
  }, []);

  // ── Voice Recording Controls ──
  const startRecordingAudio = async () => {
    try {
      if (isAIPlaying) window.speechSynthesis.cancel();
      browserSpeechTextRef.current = "";
      try {
        recognitionRef.current?.start();
      } catch (_) {}

      await audioRecorderRef.current.start((secs) => setRecordDuration(secs));
      setIsRecording(true);
      setIsPaused(false);

      // Start volume meter animation
      const updateVolume = () => {
        if (audioRecorderRef.current) {
          const vol = audioRecorderRef.current.getVolume();
          setVolumeLevel(vol);
          animFrameRef.current = requestAnimationFrame(updateVolume);
        }
      };
      updateVolume();
    } catch (err) {
      console.error("Audio recording start error:", err);
    }
  };

  const pauseRecordingAudio = () => {
    audioRecorderRef.current?.pause();
    setIsPaused(true);
  };

  const resumeRecordingAudio = () => {
    audioRecorderRef.current?.resume();
    setIsPaused(false);
  };

  const stopAndTranscribeAudio = async () => {
    if (!audioRecorderRef.current) return;
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    try {
      recognitionRef.current?.stop();
    } catch (_) {}

    setIsRecording(false);
    setIsPaused(false);
    setTranscribing(true);

    try {
      const { blob } = await audioRecorderRef.current.stop();
      let transcribed = false;

      if (blob && blob.size > 0) {
        try {
          const res = await transcribeAudio(blob, "candidate_response.webm");
          if (res?.transcript) {
            setAnswer((prev) => (prev.trim() ? prev + " " + res.transcript : res.transcript));
            transcribed = true;
          }
        } catch (serverErr) {
          console.warn("Server transcription notice, falling back to browser speech engine:", serverErr);
        }
      }

      if (!transcribed && browserSpeechTextRef.current) {
        setAnswer((prev) => (prev.trim() ? prev + " " + browserSpeechTextRef.current : browserSpeechTextRef.current));
      }
    } catch (err) {
      console.error("Transcription error:", err);
      if (browserSpeechTextRef.current) {
        setAnswer((prev) => (prev.trim() ? prev + " " + browserSpeechTextRef.current : browserSpeechTextRef.current));
      }
    } finally {
      setTranscribing(false);
      setRecordDuration(0);
      setVolumeLevel(0);
    }
  };

  const cancelRecordingAudio = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    try {
      recognitionRef.current?.stop();
    } catch (_) {}
    audioRecorderRef.current?.cancel();
    setIsRecording(false);
    setIsPaused(false);
    setRecordDuration(0);
    setVolumeLevel(0);
  };


  // ── Camera Toggle ──
  const toggleCamera = async () => {
    if (cameraOn) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      setCameraOn(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        streamRef.current = stream;
        setCameraOn(true);
        setTimeout(() => {
          if (userVideoRef.current) userVideoRef.current.srcObject = stream;
        }, 100);
      } catch {
        setCameraOn(false);
      }
    }
  };

  // ── Speak AI Question / Feedback ──
  const speakText = (text) =>
    new Promise((resolve) => {
      if (!window.speechSynthesis || !selectedVoice || !text?.trim()) {
        resolve();
        return;
      }

      window.speechSynthesis.cancel();

      setTimeout(() => {
        const utter = new SpeechSynthesisUtterance(
          text.replace(/,/g, ", ... ").replace(/\./g, ". ... ")
        );
        utter.voice = selectedVoice;
        utter.rate = 0.92;
        utter.pitch = 1.05;
        utter.volume = 1;
        utter.onstart = () => {
          setIsAIPlaying(true);
          aiVideoRef.current?.play();
        };
        utter.onend = () => {
          aiVideoRef.current?.pause();
          if (aiVideoRef.current) aiVideoRef.current.currentTime = 0;
          setIsAIPlaying(false);
          setTimeout(() => {
            setSubtitle("");
            resolve();
          }, 300);
        };
        setSubtitle(text);
        window.speechSynthesis.speak(utter);
      }, 150);
    });

  // ── Welcome & Intro ──
  useEffect(() => {
    if (!selectedVoice || introSpoken) return;
    const runIntro = async () => {
      setIntroSpoken(true);
      await new Promise((r) => setTimeout(r, 1200));
      await speakText(`Welcome ${userName.split(" ")[0]}! Let's begin your interview.`);
      await new Promise((r) => setTimeout(r, 900));
      await speakText(interviewData.question?.question || "");
    };
    runIntro();
  }, [selectedVoice]);

  // ── Speak on question change ──
  useEffect(() => {
    if (!introSpoken || !selectedVoice || !question?.question) return;
    const speak = async () => {
      await new Promise((r) => setTimeout(r, 900));
      await speakText(question.question);
    };
    speak();
  }, [question]);

  // ── Sync interviewData ──
  useEffect(() => {
    if (interviewData.question) {
      setQuestion(interviewData.question);
      setCurrentIndex(interviewData.currentQuestion || 0);
      setTimeLeft(interviewData.question.timer || 60);
      setTimerActive(true);
    }
  }, [interviewData]);

  // ── Timer countdown ──
  useEffect(() => {
    if (timeLeft <= 0 || !timerActive) return;
    const t = setInterval(() => setTimeLeft((p) => p - 1), 1000);
    return () => clearInterval(t);
  }, [timeLeft, timerActive]);

  // ── Submit Answer ──
  const submit = async () => {
    if (!answer.trim() || loading) return;

    if (isRecording) {
      await stopAndTranscribeAudio();
    }

    try {
      setTimerActive(false);
      setLoading(true);
      const res = await submitAnswer({
        interviewId: interviewData.interviewId,
        answer: answer.trim(),
      });

      if (res.completed) {
        setFeedback(res.feedback || null);
        await new Promise((r) => setTimeout(r, 700));
        await speakText(
          res.feedback?.feedback || "Great job! Your interview is complete. Preparing your report now."
        );
        setLoading(false);
        navigate(`/interview/${interviewData.interviewId}/report`);
        return;
      }

      setFeedback(res.feedback);
      await new Promise((r) => setTimeout(r, 700));
      await speakText(
        res.feedback?.feedback || "Noted your answer. Let's move to the next question."
      );

      setLoading(false);
      setQuestion(res.question);
      setCurrentIndex(res.currentQuestion);
      setTimeLeft(res.question?.timer || 60);
      setTimerActive(true);
      setAnswer("");
      setFeedback(null);
    } catch (err) {
      console.error("Submit answer failed:", err);
      alert(err.response?.data?.detail || err.response?.data?.message || "Failed to submit answer. Please try again.");
      setLoading(false);
      setTimerActive(true);
    }
  };

  const handleCodeSubmit = (code) => {
    setAnswer((prev) => {
      const separator = prev.trim() ? "\n\n--- Code Solution ---\n" : "--- Code Solution ---\n";
      return prev + separator + code;
    });
    setCodeOpen(false);
  };

  const formatSecs = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-3 sm:p-5 font-sans">
      {/* Code Editor Popup */}
      <CodeEditorPanel
        open={codeOpen}
        onClose={() => setCodeOpen(false)}
        onSubmitCode={handleCodeSubmit}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-5xl bg-[#0E1016] border border-white/10 rounded-3xl overflow-hidden shadow-2xl grid lg:grid-cols-[36%_64%]"
      >
        {/* ── LEFT: AI Video + User Camera + Controls ── */}
        <div className="flex flex-col border-b lg:border-b-0 lg:border-r border-white/8 p-4 sm:p-5 gap-3.5">
          {/* AI Video Container */}
          <div className="relative rounded-2xl overflow-hidden bg-black aspect-video border border-white/10 shadow-md">
            <video
              ref={aiVideoRef}
              src={videoSource}
              muted
              playsInline
              preload="auto"
              loop
              className="w-full h-full object-cover"
            />
            {isAIPlaying && (
              <div className="absolute bottom-2 left-2 flex items-center gap-1.5 bg-black/70 backdrop-blur-md rounded-full px-3 py-1 border border-white/10">
                <div className="flex gap-1 items-end h-3">
                  {[1, 2, 3].map((i) => (
                    <motion.div
                      key={i}
                      className="w-0.5 bg-indigo-400 rounded-full"
                      animate={{ height: ["4px", "12px", "4px"] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                    />
                  ))}
                </div>
                <span className="text-[11px] font-bold text-white/90">AI Speaking</span>
              </div>
            )}
          </div>

          {/* AI Subtitles */}
          <div className="min-h-[48px] flex items-center">
            <AnimatePresence>
              {subtitle && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"
                >
                  <p className="text-xs text-slate-300 leading-relaxed text-center">{subtitle}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* User Video Frame */}
          <div className="relative rounded-2xl overflow-hidden bg-[#17181E] border border-white/8 aspect-video flex items-center justify-center">
            {cameraOn ? (
              <>
                <video
                  ref={userVideoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-full object-cover scale-x-[-1]"
                />
                <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm rounded-full px-2.5 py-0.5 border border-white/10">
                  <span className="text-[10px] font-semibold text-white/80">You</span>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <div className="w-14 h-14 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xl">
                  {userInitial}
                </div>
                <span className="text-xs text-slate-400">{userName.split(" ")[0]}</span>
              </div>
            )}
          </div>

          {/* Media Action Buttons */}
          <div className="flex items-center justify-center gap-3 pt-1">
            <button
              onClick={toggleCamera}
              className={`p-2.5 rounded-xl border transition cursor-pointer ${
                cameraOn ? "bg-white/15 border-white/20 text-white" : "bg-white/5 border-white/10 text-slate-400 hover:text-white"
              }`}
              title="Toggle Camera"
            >
              {cameraOn ? <FiCamera size={16} /> : <FiCameraOff size={16} />}
            </button>

            <button
              onClick={() => setCodeOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl border bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 transition cursor-pointer text-xs font-semibold"
              title="Open Coding Editor"
            >
              <FiCode size={14} className="text-indigo-400" />
              <span>Code Editor</span>
            </button>
          </div>
        </div>

        {/* ── RIGHT: Question + Voice Waveform + Answer ── */}
        <div className="flex flex-col p-4 sm:p-6 justify-between space-y-4">
          {/* Question Header & Timer */}
          <div>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  <span>AI Mock Interview</span>
                  <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {question?.type || "Technical"}
                  </span>
                </h2>
                <div className="flex items-center gap-2 text-slate-400 text-xs mt-1">
                  <FiClock size={12} />
                  <span>Difficulty: {question?.difficulty || "Medium"}</span>
                </div>
              </div>

              <Timer timeLeft={timeLeft} totalTime={question?.timer || 60} />
            </div>

            {/* Question Text Box */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              key={question?.question}
              className="relative overflow-hidden rounded-2xl bg-[#17181E] border border-white/10 p-4 sm:p-5"
            >
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0">
                  <FiMessageSquare size={14} />
                </div>
                <p className="text-xs font-bold text-slate-400">
                  Question {currentIndex + 1} of {totalQuestions}
                </p>
              </div>
              <p className="text-slate-100 text-sm sm:text-base leading-relaxed font-medium">
                {question?.question}
              </p>
            </motion.div>
          </div>

          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Interview Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* ── Server-Side Voice Recorder Box ── */}
          <div className="bg-[#17181E] border border-white/10 rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <FiMic className="text-indigo-400" />
                <span>Voice Answer (Server-Side Whisper STT)</span>
              </span>

              {isRecording && (
                <span className="flex items-center gap-1.5 text-xs font-bold text-rose-400 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  REC {formatSecs(recordDuration)}
                </span>
              )}
            </div>

            {/* Live Audio Waveform when recording */}
            {isRecording && (
              <div className="flex items-center justify-center gap-1 h-8 bg-black/40 rounded-xl px-4">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-indigo-400 rounded-full transition-all duration-75"
                    style={{
                      height: `${Math.max(4, Math.min(28, (volumeLevel / 255) * 32 * (0.4 + (i % 5) * 0.2)))}px`,
                    }}
                  />
                ))}
              </div>
            )}

            {/* Voice Action Buttons */}
            <div className="flex items-center gap-2">
              {!isRecording ? (
                <button
                  type="button"
                  onClick={startRecordingAudio}
                  disabled={transcribing}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition cursor-pointer disabled:opacity-50"
                >
                  <FiMic size={14} />
                  <span>Start Voice Recording</span>
                </button>
              ) : (
                <>
                  {isPaused ? (
                    <button
                      type="button"
                      onClick={resumeRecordingAudio}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition cursor-pointer"
                    >
                      <FiPlay size={12} />
                      <span>Resume</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={pauseRecordingAudio}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white font-bold text-xs transition cursor-pointer"
                    >
                      <FiPause size={12} />
                      <span>Pause</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={stopAndTranscribeAudio}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition cursor-pointer shadow-xs"
                  >
                    <FiSquare size={12} />
                    <span>Done &amp; Transcribe</span>
                  </button>

                  <button
                    type="button"
                    onClick={cancelRecordingAudio}
                    className="p-2 rounded-xl hover:bg-rose-500/20 text-rose-400 transition cursor-pointer"
                    title="Cancel Recording"
                  >
                    <FiRotateCcw size={13} />
                  </button>
                </>
              )}

              {transcribing && (
                <span className="text-xs text-indigo-400 font-semibold flex items-center gap-1.5 animate-pulse ml-auto">
                  <div className="w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
                  Transcribing audio with Whisper AI...
                </span>
              )}
            </div>
          </div>

          {/* Editable Answer Textarea */}
          <div className="flex-1 flex flex-col min-h-[110px]">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Your Answer (Editable before submitting)
              </label>
              <span className="text-[11px] text-slate-500">
                {answer.length} characters
              </span>
            </div>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => {
                if (e.ctrlKey && e.key === "Enter") submit();
              }}
              rows={4}
              placeholder="Speak using the voice recorder above or type your answer here..."
              className="w-full rounded-2xl bg-[#17181E] border border-white/10 p-4 text-xs sm:text-sm text-slate-100 outline-none resize-none focus:border-indigo-500 transition placeholder:text-slate-500 leading-relaxed"
            />
          </div>

          {/* AI Turn Feedback Modal / Banner */}
          <AnimatePresence>
            {feedback && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 max-h-32 overflow-y-auto"
              >
                <p className="text-[11px] uppercase tracking-wider font-extrabold text-emerald-400 mb-1 flex items-center gap-1">
                  <FiZap size={13} />
                  <span>AI Real-time Feedback</span>
                </p>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {feedback.feedback || "Answer evaluated successfully."}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bottom Submit Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-white/8">
            <span className="text-xs text-slate-500 hidden sm:block">
              Press <kbd className="mx-1 rounded bg-white/10 px-1.5 py-0.5 text-slate-300 text-[10px]">Ctrl+Enter</kbd> to submit answer
            </span>

            <button
              disabled={loading || !answer.trim()}
              onClick={submit}
              className="ml-auto h-11 min-w-[160px] px-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition disabled:opacity-40 cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  <span>Evaluating Answer...</span>
                </>
              ) : (
                <>
                  <span>Submit Answer</span>
                  <FiArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default Step2Interview;