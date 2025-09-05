# 🚀 Hireloom – Autonomous Hiring Intelligence Agent  

Hireloom is an **end-to-end autonomous hiring platform** built for the **AI & Productivity track** of Recurzive V2.  
It combines multiple **AI agents** into a single pipeline that automates **job posting, candidate evaluation, scheduling, and interview intelligence** – freeing recruiters to focus on decisions, not logistics.  

---

## 🌟 Features    

- **Agentic Pipeline** (5 AI Agents):  
  1. **Resume Parser** → Parses resumes + GitHub repos to evaluate candidate relevance.  
  2. **Assessment Agent** → Generates and manages MCQs for skill validation.  
  3. **Ranking Agent** → Ranks candidates based on assessment + profile scores.  
  4. **Communication Agent** → Uses WhatsApp/Telegram to confirm availability and interest.  
  5. **Scheduler Agent** → Cross-checks recruiter’s calendar, schedules interviews, and creates **Google Meet links**.  
  6. **Call Intelligence Agent** → Records & transcribes interviews, creates candidate flashcards, captures recruiter notes, and analyzes cultural fit.  

- **Analytical Dashboard**  
  Provides recruiters with **scores, rankings, notes, and progress tracking** in a mission-control view.  

---

## 🏗️ System Design  

Data Input → Parsing → Ranking → Communication → Scheduling → Call Intelligence → Analytical Dashboard → Data Output
Each step is powered by **specialized AI agents**, orchestrated through **LangChain**.  

---

## 🛠️ Tech Stack  

- **Frontend** → [Next.js](https://nextjs.org/) (Recruiter dashboard & candidate interface)  
- **Backend** → [FastAPI](https://fastapi.tiangolo.com/) (API layer & agent orchestration)  
- **AI Orchestration** → [LangChain](https://www.langchain.com/) (manages AI agent pipeline)  
- **Database** → [Firestore](https://firebase.google.com/docs/firestore) (resume data, rankings, scheduling)  
- **Authentication** → [Firebase Auth](https://firebase.google.com/docs/auth) (secure login)  
- **LLM Layer** → [Gemini API](https://ai.google.dev/gemini-api) (summarization, ranking, flashcards, insights)  

---

## ⚡ Standout Factors  

- **End-to-End Automation** → From job posting to offers, all in one pipeline.  
- **Calendar-Aware Scheduling** → AI schedules meetings *in-chat*, creates Meet links automatically.  
- **Beyond the Resume** → GitHub analysis, assessments, and behavioral insights for a 360° candidate profile.  
- **Unified Experience** → Replaces multiple tools (LinkedIn, Calendly, ATS, WhatsApp) with one seamless platform.  

---

## 🚀 Getting Started  

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hireloom.git
cd hireloom
```
### 2.Backend Setup (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
### 3. Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev
```
---

## 📊 Workflow Overview  

- **Recruiter posts a job** → Agent posts on external platforms.  
- **Candidates apply** → Resumes parsed & GitHub repos analyzed.  
- **Assessments auto-generated** → Candidates ranked.  
- **Communication agent** → Reaches out via WhatsApp/Telegram.  
- **Scheduler** → Books interviews and auto-creates Google Meet links.  
- **Call Intelligence** → Captures insights and updates recruiter dashboard.  

---

## 👨‍💻 Team  

- [**SpaceTesla**](https://github.com/SpaceTesla)  
- [**areebahmeddd**](https://github.com/areebahmeddd)  
- [**hemamalinii**](https://github.com/hemamalinii)  
- [**kThendral**](https://github.com/kThendral)  

Hackathon builders of **Hireloom** 💡  

---
##📜 License

This project is licensed under the MIT License.






