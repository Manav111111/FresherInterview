import api from "../utils/axios";

/**
 * Intelligent client-side fallback knowledge engine
 * Generates verified, actionable answers with direct navigation links if the backend is cold or unreachable.
 */
const getClientSideFallback = (query = "", context = {}) => {
  const q = query.toLowerCase().trim();
  const role = context.target_role || "Software Engineer";

  if (
    q.includes("fresher.ai") ||
    q.includes("what is") ||
    q.includes("prepare for jobs") ||
    q.includes("how can it help") ||
    q.includes("features") ||
    q.includes("platform") ||
    q.includes("how does")
  ) {
    return {
      success: true,
      reply:
        `**Fresher.AI** is an AI-powered career readiness platform designed to help students and early-career developers land their dream tech jobs.\n\n` +
        `Here is how Fresher.AI accelerates your preparation:\n` +
        `• **AI Mock Interviews** (\`/interview\`): Practice realistic, adaptive technical interviews tailored to ${role} with live speech recognition and multi-criteria scoring rubrics.\n` +
        `• **ATS Resume Scorer** (\`/scorer\`): Upload your resume to benchmark ATS compatibility, discover missing skills, and receive recruiter-grade bullet rewrites.\n` +
        `• **Personalized Career Roadmaps** (\`/roadmap\`): Generate weekly learning paths with curated YouTube creators, GitHub projects, and official docs.\n` +
        `• **Whiteboard Solution Videos** (\`/solution-video\`): Watch step-by-step whiteboard animation videos with voice narration explaining complex algorithms and concepts.\n\n` +
        `Where would you like to start today?`,
      intent: "website_information",
      links: [
        { name: "🎤 Start AI Mock Interview", path: "/interview", description: "Adaptive mock interviews" },
        { name: "📄 Score My Resume", path: "/scorer", description: "ATS Resume Scorer" },
        { name: "🗺️ Build Learning Roadmap", path: "/roadmap", description: "Custom weekly curriculum" },
        { name: "📺 Solution Videos", path: "/solution-video", description: "Animated whiteboard explanations" },
      ],
      suggested_actions: [
        "Start an AI Interview",
        "Analyze My Resume",
        "Build Learning Roadmap",
        "Explore Solution Videos",
      ],
    };
  }

  if (q.includes("resume") || q.includes("ats") || q.includes("scorer") || q.includes("cv")) {
    return {
      success: true,
      reply:
        `Our **ATS Resume Scorer** scans your technical resume against modern tech industry benchmarks.\n\n` +
        `**What it provides:**\n` +
        `• **Overall ATS Match Score** (0-100)\n` +
        `• **Detected & Missing Core Skills** for your target role\n` +
        `• **Action-Verb & Metric Bullet Rewrites** to improve recruiter impact\n` +
        `• **Formatting & Structure Audit** to ensure ATS parsers read your resume cleanly.`,
      intent: "resume_help",
      links: [
        { name: "📄 Open ATS Resume Scorer", path: "/scorer", description: "Analyze your tech resume" },
        { name: "✏️ Interactive Resume Builder", path: "/resume", description: "Create a modern tech resume" },
      ],
      suggested_actions: ["Analyze My Resume", "What skills am I missing?", "Start an AI Interview"],
    };
  }

  if (q.includes("interview") || q.includes("practice") || q.includes("mock") || q.includes("question")) {
    return {
      success: true,
      reply:
        `Fresher.AI's **Adaptive AI Mock Interview** evaluates your technical depth, reasoning, and communication.\n\n` +
        `**How it works:**\n` +
        `1. Choose your role (e.g. ${role}) and target experience level.\n` +
        `2. Answer dynamic technical and behavioral questions via microphone speech or text.\n` +
        `3. Receive instant rubric evaluations, partial credit analysis, and actionable feedback after every turn.`,
      intent: "interview_help",
      links: [
        { name: "🎤 Start AI Mock Interview", path: "/interview", description: "Practice role-specific mock interview" },
        { name: "📊 View Performance Analytics", path: "/performance", description: "Check interview readiness scores" },
      ],
      suggested_actions: ["Start an AI Interview", "How does partial credit work?", "Analyze My Resume"],
    };
  }

  if (q.includes("roadmap") || q.includes("learn") || q.includes("study") || q.includes("curriculum")) {
    return {
      success: true,
      reply:
        `Our **Career Roadmap Generator** analyzes your skill gaps and builds a customized week-by-week engineering roadmap.\n\n` +
        `Each weekly milestone includes:\n` +
        `• **Core Concepts** to master\n` +
        `• **Curated YouTube Tutorials** from top industry educators\n` +
        `• **Hands-On Portfolio Projects** to build and showcase on GitHub\n` +
        `• **Interactive Knowledge Checks** to verify retention.`,
      intent: "roadmap_help",
      links: [
        { name: "🗺️ Generate Career Roadmap", path: "/roadmap", description: "Build personalized learning path" },
      ],
      suggested_actions: ["Build Learning Roadmap", "Start an AI Interview", "Analyze My Resume"],
    };
  }

  if (q.includes("video") || q.includes("solution") || q.includes("whiteboard") || q.includes("explain")) {
    return {
      success: true,
      reply:
        `The **AI Solution Video Generator** converts any technical question, equation, or algorithm into a step-by-step whiteboard animation video with natural voice narration.\n\n` +
        `Try entering a problem like *'Solve 2x + 5 = 15'* or *'How does Binary Search work?'* to see it in action!`,
      intent: "solution_video",
      links: [
        { name: "📺 Open Solution Video Studio", path: "/solution-video", description: "Generate whiteboard video solutions" },
      ],
      suggested_actions: ["Explore Solution Videos", "Start an AI Interview", "Build Learning Roadmap"],
    };
  }

  // Default fallback
  return {
    success: true,
    reply:
      `I am here to help you navigate Fresher.AI, prepare for technical interviews, analyze your resume, and master core engineering concepts for **${role}**.\n\n` +
      `What would you like to explore?`,
    intent: "general",
    links: [
      { name: "🎤 AI Mock Interview", path: "/interview", description: "Practice mock interview" },
      { name: "📄 Resume Scorer", path: "/scorer", description: "Score your resume" },
      { name: "🗺️ Career Roadmap", path: "/roadmap", description: "Custom learning roadmap" },
    ],
    suggested_actions: [
      "How does Fresher.AI work?",
      "Start an AI Interview",
      "Analyze My Resume",
      "Build Learning Roadmap",
    ],
  };
};

/**
 * Sends a message to the AI Chatbot with intent classification and resilient fallback.
 * @param {string} message - User message
 * @param {Array} history - Message history
 * @param {Object} context - User context (name, target_role)
 */
export const sendChatMessage = async (message, history = [], context = {}) => {
  const cleanMsg = (message || "").trim();
  if (!cleanMsg) {
    return getClientSideFallback("", context);
  }

  // Attempt 1: Call FastAPI backend
  try {
    const response = await api.post(
      "/api/chat/message",
      {
        message: cleanMsg,
        history,
        context,
      },
      { timeout: 25000 }
    );

    if (response?.data && response.data.reply) {
      return response.data;
    }
  } catch (error) {
    console.warn("Primary chat API attempt failed, trying retry...", error.message);
  }

  // Attempt 2: Single immediate retry
  try {
    const retryRes = await api.post(
      "/api/chat/message",
      {
        message: cleanMsg,
        history,
        context,
      },
      { timeout: 15000 }
    );

    if (retryRes?.data && retryRes.data.reply) {
      return retryRes.data;
    }
  } catch (retryError) {
    console.warn("Chat API retry notice, using grounded fallback:", retryError.message);
  }

  // Resilient fallback: Provide verified grounded answer matching user intent
  return getClientSideFallback(cleanMsg, context);
};
