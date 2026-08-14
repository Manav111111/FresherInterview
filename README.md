# FresherInterview

AI-powered career acceleration and mock interview platform for students and fresh graduates.

## Tech Stack
- **Frontend:** React, Vite, Tailwind CSS / Vanilla CSS, Lucide Icons, Redux Toolkit
- **Backend:** FastAPI (Python), LangGraph, LangChain Groq (LLaMA 3.3 70B), Supabase (PostgreSQL + JSONB), Redis
- **Authentication:** Firebase Auth / Supabase Auth & Session Cookies
- **Payments:** Razorpay

## Getting Started

### 1. Backend Setup
```bash
cd backend_fastapi
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in Supabase, Groq, and Redis keys in .env
uvicorn app.main:app --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
