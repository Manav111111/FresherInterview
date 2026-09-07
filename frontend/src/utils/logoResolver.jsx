import React, { useState } from "react";
import {
  FiCode,
  FiDatabase,
  FiServer,
  FiCpu,
  FiGlobe,
  FiLayers,
  FiTerminal,
  FiCloud,
  FiPlayCircle,
  FiBookOpen,
  FiBookmark,
} from "react-icons/fi";

// =========================================================================
// 1. PRIMARY LOCAL AND CDN LOGO MAPPINGS
// Prioritize local dedicated SVGs for products that CDNs confuse or lack.
// =========================================================================
const LOCAL_LOGOS = {
  langgraph: "/logos/langgraph.svg",
  fastmcp: "/logos/fastmcp.svg",
  groq: "/logos/groq.svg",
  qdrant: "/logos/qdrant.svg",
  gemini: "/logos/gemini.svg",
  openai: "/logos/openai.svg",
  claude: "/logos/claude.svg",
  huggingface: "/logos/huggingface.svg",
  antigravity: "/logos/antigravity.svg",
};

const CDN_LOGOS = {
  // Languages & Runtimes
  python: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg",
  typescript: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg",
  javascript: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg",
  nodejs: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nodejs/nodejs-original.svg",

  // AI & Agentic Frameworks
  langchain: "https://cdn.simpleicons.org/langchain/1C3C3C",
  tensorflow: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tensorflow/tensorflow-original.svg",
  pytorch: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytorch/pytorch-original.svg",
  scikitlearn: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/scikitlearn/scikitlearn-original.svg",
  colab: "https://cdn.simpleicons.org/googlecolab/F9AB00",
  pydantic: "https://cdn.simpleicons.org/pydantic/E92063",
  logfire: "https://cdn.simpleicons.org/pydantic/E92063",

  // Backend & Web Frameworks
  fastapi: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg",
  flask: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/flask/flask-original.svg",
  django: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/django/django-plain.svg",
  express: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/express/express-original.svg",

  // Frontend & UI
  react: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original.svg",
  nextjs: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nextjs/nextjs-original.svg",
  tailwind: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tailwindcss/tailwindcss-original.svg",
  vite: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vite/vite-original.svg",

  // Mobile
  flutter: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/flutter/flutter-original.svg",
  expo: "https://cdn.simpleicons.org/expo/000020",
  android: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/android/android-original.svg",
  androidstudio: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/androidstudio/androidstudio-original.svg",
  playstore: "/google-play-store-logo-svgrepo-com.svg",

  // Databases & Caching
  postgresql: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg",
  mongodb: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mongodb/mongodb-original.svg",
  supabase: "https://cdn.simpleicons.org/supabase/3ECF8E",
  firebase: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/firebase/firebase-plain.svg",
  redis: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/redis/redis-original.svg",
  prisma: "https://cdn.simpleicons.org/prisma/2D3748",

  // DevOps & Cloud
  docker: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg",
  kubernetes: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kubernetes/kubernetes-plain.svg",
  aws: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/amazonwebservices/amazonwebservices-original-wordmark.svg",
  vercel: "https://cdn.simpleicons.org/vercel/000000",
  git: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg",
  github: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg",
  linux: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linux/linux-original.svg",
  postman: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postman/postman-original.svg",

  // Design, Payments & Career
  figma: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/figma/figma-original.svg",
  stripe: "https://cdn.simpleicons.org/stripe/635BFF",
  razorpay: "https://cdn.simpleicons.org/razorpay/0C2340",
  kaggle: "https://cdn.simpleicons.org/kaggle/20BEFF",
  linkedin: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg",
  wellfound: "https://cdn.simpleicons.org/wellfound/000000",
  geeksforgeeks: "https://cdn.simpleicons.org/geeksforgeeks/2F8D46",
  leetcode: "https://cdn.simpleicons.org/leetcode/FFA116",
  youtube: "https://cdn.simpleicons.org/youtube/FF0000",
  freecodecamp: "https://cdn.simpleicons.org/freecodecamp/0A0A23",
  deeplearningai: "https://cdn.simpleicons.org/coursera/0056D2",
};

/**
 * Normalizes input key or name into a canonical lookup key.
 */
export function normalizeLogoKey(keyOrName) {
  if (!keyOrName) return "generic";
  const k = String(keyOrName).toLowerCase().replace(/[^a-z0-9]/g, "");

  // Synonyms & Aliases
  if (k.includes("langgraph")) return "langgraph";
  if (k.includes("fastmcp") || k.includes("mcp")) return "fastmcp";
  if (k.includes("groq")) return "groq";
  if (k.includes("qdrant")) return "qdrant";
  if (k.includes("langchain")) return "langchain";
  if (k.includes("gemini") || k.includes("googlegemini")) return "gemini";
  if (k.includes("openai") || k.includes("chatgpt")) return "openai";
  if (k.includes("claude") || k.includes("anthropic")) return "claude";
  if (k.includes("huggingface") || k.includes("hf")) return "huggingface";
  if (k.includes("pytorch")) return "pytorch";
  if (k.includes("tensorflow") || k.includes("tf")) return "tensorflow";
  if (k.includes("scikitlearn") || k.includes("sklearn")) return "scikitlearn";
  if (k.includes("colab")) return "colab";
  if (k.includes("python")) return "python";
  if (k.includes("typescript") || k === "ts") return "typescript";
  if (k.includes("javascript") || k === "js") return "javascript";
  if (k.includes("fastapi")) return "fastapi";
  if (k.includes("flask")) return "flask";
  if (k.includes("django")) return "django";
  if (k.includes("nextjs") || k === "next") return "nextjs";
  if (k.includes("reactnative")) return "react";
  if (k.includes("react")) return "react";
  if (k.includes("nodejs") || k === "node") return "nodejs";
  if (k.includes("express")) return "express";
  if (k.includes("tailwind")) return "tailwind";
  if (k.includes("vite")) return "vite";
  if (k.includes("flutter")) return "flutter";
  if (k.includes("expo")) return "expo";
  if (k.includes("androidstudio")) return "androidstudio";
  if (k.includes("android")) return "android";
  if (k.includes("playstore") || k.includes("googleplay")) return "playstore";
  if (k.includes("postgres") || k.includes("psql") || k.includes("sql")) return "postgresql";
  if (k.includes("mongodb") || k.includes("mongo")) return "mongodb";
  if (k.includes("supabase")) return "supabase";
  if (k.includes("firebase")) return "firebase";
  if (k.includes("redis")) return "redis";
  if (k.includes("prisma")) return "prisma";
  if (k.includes("docker")) return "docker";
  if (k.includes("kubernetes") || k.includes("k8s")) return "kubernetes";
  if (k.includes("aws") || k.includes("amazon")) return "aws";
  if (k.includes("vercel")) return "vercel";
  if (k.includes("github")) return "github";
  if (k.includes("git")) return "git";
  if (k.includes("linux") || k.includes("ubuntu")) return "linux";
  if (k.includes("postman")) return "postman";
  if (k.includes("figma")) return "figma";
  if (k.includes("pydantic")) return "pydantic";
  if (k.includes("logfire")) return "logfire";
  if (k.includes("stripe")) return "stripe";
  if (k.includes("razorpay")) return "razorpay";
  if (k.includes("kaggle")) return "kaggle";
  if (k.includes("linkedin")) return "linkedin";
  if (k.includes("wellfound") || k.includes("angellist")) return "wellfound";
  if (k.includes("geeksforgeeks") || k === "gfg") return "geeksforgeeks";
  if (k.includes("leetcode")) return "leetcode";
  if (k.includes("youtube")) return "youtube";

  return k;
}

/**
 * Resolves a logoKey into a prioritized URL.
 * 1. Local explicit assets (/logos/...)
 * 2. Devicon / SimpleIcons CDN
 * 3. Null (will trigger generic icon fallback)
 */
export function resolveLogo(logoKey, name) {
  const normKey = normalizeLogoKey(logoKey || name);
  if (LOCAL_LOGOS[normKey]) {
    return LOCAL_LOGOS[normKey];
  }
  if (CDN_LOGOS[normKey]) {
    return CDN_LOGOS[normKey];
  }
  return null;
}

/**
 * Returns a fallback vector icon based on technology category or name.
 */
function getGenericIcon(name, size = 18) {
  const n = String(name || "").toLowerCase();
  if (n.includes("data") || n.includes("sql") || n.includes("store")) {
    return <FiDatabase size={size} className="text-sky-600" />;
  }
  if (n.includes("server") || n.includes("api") || n.includes("backend")) {
    return <FiServer size={size} className="text-indigo-600" />;
  }
  if (n.includes("ai") || n.includes("model") || n.includes("learning") || n.includes("neural")) {
    return <FiCpu size={size} className="text-purple-600" />;
  }
  if (n.includes("cloud") || n.includes("deploy")) {
    return <FiCloud size={size} className="text-amber-600" />;
  }
  if (n.includes("terminal") || n.includes("cli") || n.includes("bash")) {
    return <FiTerminal size={size} className="text-slate-700" />;
  }
  if (n.includes("doc") || n.includes("guide") || n.includes("book")) {
    return <FiBookOpen size={size} className="text-emerald-600" />;
  }
  if (n.includes("video") || n.includes("youtube") || n.includes("watch")) {
    return <FiPlayCircle size={size} className="text-red-600" />;
  }
  return <FiCode size={size} className="text-indigo-600" />;
}

/**
 * Centralized Logo Component:
 * Resolves logoKey -> renders clean image.
 * If image fails to load, gracefully falls back to vector React icon.
 * NEVER renders a broken image box!
 */
export function TechLogo({
  logoKey,
  name,
  className = "w-6 h-6 object-contain",
  size = 20,
}) {
  const [failed, setFailed] = useState(false);
  const logoUrl = resolveLogo(logoKey, name);

  if (!logoUrl || failed) {
    return (
      <div className="flex items-center justify-center">
        {getGenericIcon(name || logoKey, size)}
      </div>
    );
  }

  return (
    <img
      src={logoUrl}
      alt={name || logoKey || "Technology logo"}
      className={className}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

export default TechLogo;
