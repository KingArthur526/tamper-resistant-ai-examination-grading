# 🛡️ Tamper-Resistant AI-Powered Examination Grading System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Bundler-Vite_6-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PyTorch](https://img.shields.io/badge/AI%2FML-Sentence--Transformers-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://www.sbert.net/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

An enterprise-grade, explainable, and cryptographically auditable examination grading platform designed for universities, academic institutions, and examination boards. Combines handwriting OCR ingestion, deterministic semantic similarity scoring against rubric concepts, spelling/lexical metrics, examiner override workflows, and SHA-256 blockchain-style hash chaining.

---

## ✨ Key Features

- **🔍 Dual-Pane Handwritten Script OCR Review**
  - Side-by-side high-resolution handwriting image inspection and interactive transcript editor.
  - Multi-page document support with per-question bounding and line confidence scoring.
- **🧠 Explainable Semantic AI Evaluation**
  - Concept-level semantic similarity scoring using Sentence-BERT (`all-MiniLM-L6-v2`) and deterministic vector embeddings.
  - Granular full-match and partial-match threshold policies.
  - Interactive **"Why this mark?"** explainability drawer breaking down matching rationale, similarity percentages, and evidence highlights.
- **✍️ Spelling & Lexical Metric Analysis**
  - Built-in spellchecker and vocabulary analyzer evaluating spelling accuracy directly as part of grading criteria.
- **🔒 Cryptographic Tamper-Resistance & Audit Ledger**
  - Continuous SHA-256 hash chaining of all grading events, mark overrides, and script uploads.
  - Automated physical disk checksum verification detecting byte-level file alteration.
  - Interactive file-tamper simulation to demonstrate real-time ledger integrity alarms.
- **👨‍🏫 Examiner In-The-Loop & Override Audit**
  - Flagged submission queue for low-confidence OCR or borderline responses.
  - Mandatory audit reason logging with previous/adjusted score delta tracking.
- **📄 Comprehensive Reporting & Analytics**
  - ReportLab PDF scorecard generation for individual candidates with integrity seals.
  - Complete CSV results matrix export for institutional record systems.
- **🎨 Obsidian & Yellow UI/UX**
  - Modern, responsive Black & Yellow design system with sleek dark mode, clear typography, and accessible contrasts.

---

## 🏗️ Architecture

```
tamper_resistant_grading/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI REST endpoints
│   │   ├── core/                # Database config & security
│   │   ├── ml/                  # Semantic similarity, OCR & explainability
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── services/            # Grading, audit & integrity services
│   ├── seed_demo.py             # Pre-configured Cambridge/DBMS exam datasets
│   ├── tests/                   # Automated pytest suite
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios API client
│   │   ├── components/          # Reusable UI components & drawers
│   │   ├── pages/               # Dashboard, Workbench, OCR, Audit & Reports
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js
├── storage/                     # Scanned scripts, OCR cache & reports
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Git**

---

### 1. Clone the Repository
```bash
git clone https://github.com/KingArthur526/tamper-resistant-ai-examination-grading.git
cd tamper-resistant-ai-examination-grading
```

---

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Seed demo examination sessions and sample handwritten scripts
python seed_demo.py

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API documentation will be accessible at: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Setup
```bash
# In a new terminal window:
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 🧪 Running Tests

Execute the automated test suite covering semantic grading, hash verification, and API endpoints:
```bash
cd backend
pytest tests/ -v
```

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite (WAL mode), Pydantic v2, PyJWT, ReportLab
- **AI / NLP:** Sentence-Transformers (`all-MiniLM-L6-v2`), PyTorch, scikit-learn, OpenCV, PyMuPDF, PySpellChecker
- **Frontend:** React 18, TypeScript, Vite 6, Tailwind CSS, Lucide Icons

---

## 👤 Author
**KingArthur526**  
GitHub: [https://github.com/KingArthur526](https://github.com/KingArthur526)

---

## 📄 License
This project is licensed under the MIT License.
