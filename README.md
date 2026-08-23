# 🚀 Fresher.AI — Next-Gen AI Mock Interview & Career Acceleration Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq_LLaMA_3.3_70B-F55036?style=for-the-badge)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/Google_Gemini_1.5-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

**Fresher.AI** is a production-grade, multimodal AI career acceleration platform tailored for students, fresh graduates, and software engineers. It delivers ultra-fast adaptive mock interviews, standardized evidence-based evaluation reports, dynamic syllabus roadmaps, an ATS resume scorecard, and an interactive AI whiteboard solution video generator.

---

## 🌟 Key Platform Features

### 🎙️ 1. Multimodal AI Mock Interview Studio
- **Adaptive AI Interviewer Avatar**: Real-time interactive avatar with dynamic video states, conversational speech synthesis, and timed question progression.
- **Voice Transcription**: High-speed speech-to-text allowing candidates to record spoken answers or type responses.
- **Dual Tracks**: Dedicated Technical Interview and HR / Behavioral tracks with resume project customization.

### 📊 2. Standardized, Evidence-Based Scoring & Final Report System
- **Strict Per-Question Rubrics**:
  - **Technical Interviews**: Technical Correctness ($40\%$), Completeness ($20\%$), Problem-Solving / Reasoning ($15\%$), Communication & Clarity ($15\%$), Relevance & Conciseness ($10\%$).
  - **HR / Behavioral Interviews**: Relevance to Question ($25\%$), Communication & Clarity ($25\%$), Answer Structure & STAR Methodology ($20\%$), Specific Real-World Examples ($15\%$), Professional Confidence ($15\%$).
- **Mathematical Difficulty-Weighted Score Aggregation**:
  $$\text{Final Score} = \frac{\sum (\text{Question Score} \times \text{Difficulty Weight})}{\sum \text{Difficulty Weight}} \quad (\text{Easy: } 0.8, \, \text{Medium: } 1.0, \, \text{Hard: } 1.2)$$
- **Standardized Result Classifications**: `🟢 Correct` ($\ge 75$), `🟡 Partially Correct` ($50\text{--}74$), `🔴 Incorrect` ($< 50$), `⚪ Insufficient` (brief/empty).
- **Comprehensive Question-by-Question Review**:
  - *Submitted Answer*
  - *What you did well* (evidence-based strengths)
  - *What was missing* (omitted concepts)
  - *What you should understand* (conceptual corrections for misconceptions)
  - *How to approach this question* (step-by-step guidance)
  - *Example of a strong answer* (model response)
- **Hiring Readiness Tiers**: Deterministically maps calculated scores to hiring tiers (*Excellent / Interview Ready*, *Strong / Nearly Ready*, *Developing / Needs Practice*, *Significant Improvement Needed*, *Fundamentals Need Attention*).
- **Topic-Wise Accuracy Breakdown**: Calculates accuracy percentages strictly across actually evaluated domain topics.

### 🛣️ 3. Dynamic Career Roadmap & Role Syllabus Generator
- **LLM-Powered Curriculum Pillars**: Generates role-specific, package-targeted syllabus pillars with granular technical topics.
- **Essential Tools & Official Links**: Dynamically suggests must-know developer platforms (GitHub, Supabase, Firebase, MongoDB, Docker, PostgreSQL, Redis, Postman) with direct links to official documentation.

### 🎬 4. AI Whiteboard Solution Video Generator
- **High-Definition Whiteboard Canvas**: Character-by-character progressive handwriting animation with step badges and accent formatting.
- **Synchronized Audio Narration**: Dynamically paces speech rate to visual scene duration for seamless voice and canvas writing synchronization.
- **Deep Technical Solutions**: Generates real mathematical, scientific, and algorithmic derivations (e.g., *Newton's Second Law $F=ma$*, *Binary Search*, *Linear Algebra*).

### 📄 5. ATS Resume Analyzer & Scorecard
- Deep ATS resume inspection detecting missing keywords, formatting errors, quantified metrics, and section completeness.
- Live interactive resume builder with dynamic PDF export.

### 🪙 6. Coin Economy & Payment System
- Rewarding progression system with coins earned through mock interviews.
- Integrated **Razorpay** checkout for premium interview packs and coin top-ups.

---

## 🏗️ Multi-Provider AI Architecture

Fresher.AI uses an intelligent multi-provider routing layer (`AIProviderRouter`):
- **Groq (LLaMA 3.3 70B Versatile)**: Primary fast engine for real-time interview question generation and instant per-question feedback.
- **Google Gemini (1.5 Flash / 1.5 Pro)**: Deep reasoning engine for multimodal analysis, ATS resume audits, and executive interview summaries.
- **Automatic Fallback & Self-Healing**: Resilient fallback handlers ensure uninterrupted mock interviews even during API outages.

```
                  ┌─────────────────────────────────────────┐
                  │          Fresher.AI Client              │
                  │   (React 19, TailwindCSS, Motion)       │
                  └────────────────────┬────────────────────┘
                                       │ HTTPS / REST
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │            FastAPI Gateway              │
                  │     (Auth, Security, Redis Cache)       │
                  └────────────────────┬────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
                ▼                                             ▼
   ┌──────────────────────────┐                  ┌──────────────────────────┐
   │    Groq Provider Router   │                  │   Gemini Provider Router  │
   │   (Fast Interview Flow)  │                  │  (Deep Reports & Analysis)│
   └────────────┬─────────────┘                  └────────────┬─────────────┘
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │     Deterministic Score Aggregator      │
                  │  (Difficulty Weights, Rubrics, Status)  │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Supabase PostgreSQL + JSONB       │
                  └─────────────────────────────────────────┘
```

---

## 💻 Tech Stack

### Frontend
- **Framework**: React 19, Vite
- **Styling**: TailwindCSS, Modern Glassmorphism & Custom CSS Tokens
- **Animations**: Motion (`motion/react`)
- **State & Routing**: React Router v7, Redux Toolkit
- **Icons**: React Icons (`fi`, `bs`, `hi2`)
- **Speech**: HTML5 Web Speech Synthesis & Recognition API

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Workflow & Agents**: LangGraph, LangChain
- **AI Providers**: Groq Cloud SDK, Google GenAI SDK
- **Database**: Supabase (PostgreSQL with JSONB storage)
- **Caching**: Redis (Session caching & rate limits)
- **Validation**: Pydantic v2 schemas
- **Auth**: Supabase Auth / Firebase JWT verification

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** (v18+)
- **Python** (v3.11+)
- **Supabase** Project & Database URL
- **Redis** Instance (Upstash or local Redis)
- **Groq API Key**
- **Google Gemini API Key**

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Manav111111/FresherInterview.git
cd FresherInterview/backend_fastapi

# Create and activate Python virtual environment
python -m venv .venv

# On Windows
.\.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env configuration file
cp .env.example .env
```

#### Backend Environment Variables (`backend_fastapi/.env`):
```env
PORT=8000
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
REDIS_URL=redis://default:password@your-redis-host:6379
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
JWT_SECRET=your_super_secret_jwt_key
```

#### Start FastAPI Server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

```bash
cd ../frontend

# Install npm packages
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` to explore the app.

---

## 🧪 Running Automated Tests

Run the complete backend test suite:
```bash
cd backend_fastapi
.\.venv\Scripts\python.exe -m pytest tests -v
```

### Verified Test Suites:
- `test_ai_router.py`: AI provider selection and strict Pydantic output validation.
- `test_interview.py`: Deterministic score aggregation, difficulty weights, classification thresholds, readiness tiers, and end-to-end interview lifecycle.
- `test_video_solution.py`: Educational whiteboard storyboard generation and math/programming validation.
- `test_roadmap.py`: Dynamic syllabus generation and must-know tool extraction.
- `test_resume.py`: Resume ATS parsing and scorecard audit.
- `test_auth.py` & `test_billing.py`: Authentication session cookies, coin economy, and Razorpay flows.

Run frontend production build validation:
```bash
cd frontend
npm run build
```

---

## 🚢 Deployment

- **Backend**: Hosted on [Render](https://render.com) (`https://fresherinterview.onrender.com`) via `render.yaml`.
- **Frontend**: Hosted on [Vercel](https://vercel.com) (`https://fresherai-silk.vercel.app`).

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
