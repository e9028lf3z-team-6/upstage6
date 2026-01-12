# Project Context: TEAM CONTEXTOR (Upstage6)

## 1. Project Overview
**TEAM CONTEXTOR** is a local web application designed to analyze manuscripts (PDF/DOCX/TXT/MD). It utilizes a multi-agent pipeline to provide deep insights into the text, including readability, tone, causality, and potential content warnings.

- **Frontend:** React (Vite) for a responsive user interface.
- **Backend:** FastAPI (Python) for API handling, document parsing, and orchestration of analysis agents.
- **Database:** SQLite for storing analysis results and document metadata.
- **Key Feature:** "Multi-Agent Analysis" which breaks down the text analysis into specialized tasks (Split, Tone, Causality, etc.).

## 2. Architecture & Tech Stack

### Backend (`/backend`)
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Package Manager:** `pip` (standard) / `uv` (implied by `uv.lock`)
- **Database:** SQLite (`backend/data/team.db`) + `aiosqlite` / `sqlalchemy`
- **Document Parsing:** `python-docx`, `pypdf`, optional Upstage API integration.
- **LLM Integration:** `openai` client (Upstage Solar LLM).

### Frontend (`/frontend`)
- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** JavaScript (`.jsx`)
- **Key Libraries:** `react-markdown` (for report rendering).

## 3. Development Workflow

### Prerequisites
- Python 3.11+
- Node.js & npm

### Backend Setup & Run
```bash
cd backend
# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# Create .env from .env.example and add UPSTAGE_API_KEY
cp .env.example .env

# Install dependencies
pip install -e .

# Run Server (Auto-reload enabled)
uvicorn main:app --reload --port 8000
```
- API Docs: http://localhost:8000/docs

### Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
- App URL: http://localhost:5173

## 4. Key Directories & Files

- **`backend/`**
    - `main.py`: Entry point for the FastAPI application.
    - `app/agents/tools/`: Analysis agents logic.
    - `app/agents/tools/report_agent.py`: **[New]** Comprehensive Report Agent (Chief Editor).
    - `app/services/pipeline_runner.py`: Orchestrates agent execution with error handling.
    - `.env.example`: **[New]** Environment variable template.
- **`frontend/`**
    - `src/App.jsx`: UI logic with Markdown report viewer.

## 5. Conventions & Notes
- **Environment Variables:**
    - `UPSTAGE_API_KEY`: Required for analysis and Upstage Document Parse.
    - `.env` files are ignored by git; use `.env.example` for reference.
- **Agent Pipeline:** The analysis is divided into specialized steps. A final "Report Agent" synthesizes all results into a human-readable format.
- **Persistence:** SQLite (`team.db`) stores analysis metadata. DB files are ignored by git.

## 6. Recent Updates (2026-01-12)

### Backend Improvements
- **Comprehensive Report Agent:** Added `report_agent.py` to synthesize results from all agents (Tone, Causality, Safety, etc.) into a professional "Chief Editor" markdown report.
- **Robust Pipeline:** Integrated `try-except` blocks in `pipeline_runner.py` to ensure the system remains stable even if individual agents fail.
- **Security & Cleanup:** 
    - Created `backend/.env.example` to prevent API key leaks.
    - Updated `.gitignore` to exclude `node_modules`, `.db` files, and `.env`.
    - Removed `node_modules` and database files from git tracking.

### Frontend Improvements
- **Markdown Rendering:** Installed `react-markdown` to display structured feedback reports from the Chief Editor agent.
- **UI Integration:** Updated `App.jsx` to prioritize the comprehensive report in the analysis results panel.

### Git Management
- All work merged into the `main` branch and pushed to the remote repository.