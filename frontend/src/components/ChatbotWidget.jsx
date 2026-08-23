import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FiMessageSquare,
  FiX,
  FiSend,
  FiCopy,
  FiCheck,
  FiMinimize2,
  FiMaximize2,
  FiChevronRight,
} from "react-icons/fi";
import { BsStars, BsLinkedin } from "react-icons/bs";

import { sendChatMessage } from "../api/chat.api";

const QUICK_PROMPTS = [
  { label: "💼 LinkedIn Post: New Job", text: "Write a LinkedIn post about starting my new role as a Software Engineer" },
  { label: "💡 Theory: What is Docker?", text: "What is Docker and why is it used in software engineering?" },
  { label: "📐 Math: Solve 2x + 5 = 15", text: "Solve the linear equation 2x + 5 = 15 step by step" },
  { label: "💻 DSA: Binary Search", text: "How does Binary Search work and what is its time complexity?" },
  { label: "🎯 Interview: Tell me about yourself", text: "How should I structure the answer for 'Tell me about yourself'?" },
];

export default function ChatbotWidget({ user }) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Hello! I am your **Fresher.AI Career & Tech Assistant**.\n\nI can help you with:\n• 💼 **Ready-to-Post LinkedIn Announcements** (jobs, internships, projects)\n• 💡 **Clear Theory & Architecture Explanations** (Docker, REST, System Design)\n• 📐 **Step-by-Step Math & Physics Solutions**\n• 🎯 **Interview Answer Strategies**\n\nHow can I help you today?",
      intent: "general",
    },
  ]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (textToSend) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || isLoading) return;

    const newMessages = [...messages, { role: "user", content: query }];
    setMessages(newMessages);
    setInputMessage("");
    setIsLoading(true);

    try {
      const history = newMessages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const context = {
        name: user?.name,
        target_role: user?.target_role || user?.role || "Software Engineer",
      };

      const res = await sendChatMessage(query, history, context);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.reply || "I'm ready for your next question!",
          intent: res.intent || "general",
        },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered a temporary connection issue. Please ask again.",
          intent: "general",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2500);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      {/* ── Floating Launcher Button ── */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.94 }}
            onClick={() => setIsOpen(true)}
            className="group relative flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-tr from-[#4F46E5] to-[#7C3AED] text-white shadow-2xl shadow-indigo-500/40 border border-white/20 transition-all cursor-pointer"
            title="Ask Fresher.AI (LinkedIn, Theory, Math & Career)"
          >
            {/* Pulsing indicator */}
            <span className="absolute -top-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border-2 border-white" />
            </span>

            <BsStars size={22} className="group-hover:rotate-12 transition-transform" />

            {/* Hover Tooltip */}
            <span className="absolute right-16 top-2.5 px-3 py-1.5 rounded-xl bg-slate-900/90 text-white text-[11px] font-semibold whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-lg backdrop-blur-xs">
              ✨ Ask AI Assistant
            </span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* ── Expandable Chat Drawer ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            className="w-[92vw] sm:w-[420px] h-[580px] max-h-[85vh] bg-white rounded-3xl border border-slate-200/90 shadow-2xl flex flex-col overflow-hidden backdrop-blur-md"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-[#4F46E5] via-[#6366F1] to-[#7C3AED] p-4 px-5 text-white flex items-center justify-between shrink-0 shadow-xs">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white border border-white/30 shadow-inner">
                  <BsStars size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold tracking-tight flex items-center gap-1.5">
                    <span>Fresher.AI Assistant</span>
                  </h3>
                  <div className="flex items-center gap-1.5 text-[10px] text-white/80 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Smart Intent Router • Ready</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/25 flex items-center justify-center text-white/90 transition cursor-pointer"
                  title="Close"
                >
                  <FiX size={17} />
                </button>
              </div>
            </div>

            {/* Quick Suggestion Chips */}
            <div className="p-2.5 px-3.5 bg-slate-50 border-b border-slate-200/80 flex items-center gap-1.5 overflow-x-auto no-scrollbar shrink-0">
              {QUICK_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(item.text)}
                  className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-[10px] font-semibold text-slate-700 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50/50 transition-all whitespace-nowrap shrink-0 shadow-2xs cursor-pointer"
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Messages Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
              {messages.map((msg, idx) => {
                const isUser = msg.role === "user";
                const isLinkedIn = msg.intent === "linkedin_post" || msg.content.includes("#");

                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`max-w-[88%] rounded-2xl p-3.5 leading-relaxed relative ${
                        isUser
                          ? "bg-[#4F46E5] text-white rounded-br-xs shadow-xs"
                          : "bg-slate-100/90 text-slate-800 rounded-bl-xs border border-slate-200/70"
                      }`}
                    >
                      {/* LinkedIn Ready-to-Post Badge */}
                      {!isUser && isLinkedIn && (
                        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/80 text-[10px] font-bold text-indigo-700">
                          <span className="flex items-center gap-1">
                            <BsLinkedin size={12} className="text-[#0A66C2]" />
                            <span>LinkedIn Ready-to-Post</span>
                          </span>
                          <button
                            onClick={() => handleCopy(msg.content, idx)}
                            className="flex items-center gap-1 text-[10px] font-bold text-indigo-600 hover:text-indigo-800 bg-white border border-indigo-200 px-2 py-0.5 rounded-md transition cursor-pointer"
                          >
                            {copiedIndex === idx ? (
                              <>
                                <FiCheck size={11} className="text-emerald-600" />
                                <span className="text-emerald-600">Copied!</span>
                              </>
                            ) : (
                              <>
                                <FiCopy size={11} />
                                <span>Copy Post</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}

                      {/* Content text */}
                      <div className="whitespace-pre-wrap font-sans">
                        {msg.content}
                      </div>

                      {/* Copy button for other assistant responses */}
                      {!isUser && !isLinkedIn && msg.content.length > 50 && (
                        <div className="pt-2 mt-2 border-t border-slate-200/50 flex justify-end">
                          <button
                            onClick={() => handleCopy(msg.content, idx)}
                            className="text-[10px] text-slate-400 hover:text-slate-600 flex items-center gap-1 transition cursor-pointer"
                          >
                            {copiedIndex === idx ? (
                              <>
                                <FiCheck size={10} className="text-emerald-600" />
                                <span className="text-emerald-600">Copied</span>
                              </>
                            ) : (
                              <>
                                <FiCopy size={10} />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}

              {/* Typing Indicator */}
              {isLoading && (
                <div className="flex items-center gap-1.5 p-3 rounded-2xl bg-slate-100 text-slate-500 w-20">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.4s]" />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Footer */}
            <div className="p-3 bg-white border-t border-slate-200/80 shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask a question or request a LinkedIn post..."
                  className="flex-1 px-4 py-2.5 rounded-2xl bg-slate-100 border border-slate-200/80 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 text-xs text-slate-900 placeholder:text-slate-400 transition"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isLoading}
                  className="w-10 h-10 rounded-2xl bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white flex items-center justify-center transition shadow-xs cursor-pointer shrink-0"
                >
                  <FiSend size={15} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
