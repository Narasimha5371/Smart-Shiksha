# 📚 Smart Shiksha

**AI-powered, multilingual educational platform designed for students in rural India.**

Smart Shiksha uses Retrieval-Augmented Generation (RAG) to deliver personalized, curriculum-aligned lessons in 5 Indian languages. It combines real-time web search with a large language model to generate comprehensive study material, quizzes, flashcards, and competitive exam preparation — all accessible from a Flutter app or a lightweight web portal.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **AI Lesson Generation** | Ask any academic question and get a detailed, structured Markdown lesson powered by Groq LLM + Google Search (RAG pipeline) |
| **30 Indian Curricula** | CBSE, ICSE, all state boards — 1,311 subjects and 17,038 chapters pre-seeded |
| **5 Languages** | English, Hindi (हिन्दी), Kannada (ಕನ್ನಡ), Telugu (తెలుగు), Tamil (தமிழ்) |
| **Quizzes** | Auto-generated chapter quizzes — MCQ, multi-select, and numerical questions |
| **Flashcards** | Quick-review flashcard decks per chapter |
| **Competitive Exam Prep** | Mock tests for JEE Mains, JEE Advanced, NEET, and Board Exams |
| **AI Tutor Chat** | Conversational tutoring on any academic topic |
| **Offline Revision** | Lessons cached locally via SQLite for offline access (desktop/mobile) |
| **Google Sign-In** | Firebase Authentication with JWT-secured API |
| **Web Portal** | Lightweight vanilla JS frontend for quick browser-based access |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Clients                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │ Flutter App  │  │  Web Portal │  │  REST Clients    │ │
│  │ (Win/Web/    │  │  (Vanilla   │  │  (Swagger /      │ │
│  │  Android)    │  │   JS)       │  │   Postman)       │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘ │
└─────────┼────────────────┼───────────────────┼───────────┘
          │                │                   │
          ▼                ▼                   ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐  │
│  │  Auth    │ │ Lessons  │ │  Quiz     │ │Competitive│  │
│  │ (Firebase│ │ (RAG)    │ │ Generator │ │ Mock Tests│  │
│  │  + JWT)  │ │          │ │           │ │           │  │
│  └──────────┘ └──────────┘ └───────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐                │
│  │ Syllabus │ │ Progress │ │  Users    │                │
│  │ Browser  │ │ Tracker  │ │  Profile  │                │
│  └──────────┘ └──────────┘ └───────────┘                │
└──────────┬───────────────────────┬───────────────────────┘
           │                       │
           ▼                       ▼
┌────────────────────┐  ┌────────────────────────────────┐
│  SQLite / Postgres │  │    External APIs                │
│  (10 tables)       │  │  • Groq (Llama 3.3 70B)        │
│                    │  │  • Serper (Google Search)       │
│                    │  │  • Firebase Auth                │
└────────────────────┘  └────────────────────────────────┘
```

---

## 📂 Project Structure

```
smartsiksha/
├── .env                          # API keys & secrets (not committed)
├── .env.example                  # Template for .env
├── .gitignore
├── README.md                     # ← you are here
├── HOW_TO_RUN.md                 # Detailed setup & run guide
│
├── backend/                      # FastAPI backend
│   ├── requirements.txt          # Python dependencies (pinned)
│   └── app/
│       ├── main.py               # App entry point, lifespan, middleware
│       ├── config.py             # Pydantic settings from .env
│       ├── auth.py               # Firebase token verification + JWT
│       ├── database.py           # SQLAlchemy async engine + sessions
│       ├── models.py             # 10 ORM models (User, Lesson, Quiz, etc.)
│       ├── schemas.py            # Pydantic request/response schemas
│       ├── routers/
│       │   ├── auth.py           # POST /api/auth/google, GET /api/auth/me
│       │   ├── lessons.py        # POST /api/ask, save/load lessons
│       │   ├── quiz.py           # Generate & fetch quizzes
│       │   ├── competitive.py    # Mock tests for JEE/NEET
│       │   ├── syllabus.py       # Browse curricula/subjects/chapters
│       │   ├── progress.py       # User progress tracking
│       │   └── users.py          # User registration & profile
│       └── services/
│           ├── groq_service.py   # Groq LLM wrapper
│           ├── serper_service.py # Google Search via Serper API
│           ├── rag_pipeline.py   # Search → Context → LLM → Response
│           └── syllabus_seed.py  # Seeds 30 curricula on first boot
│
├── flutter_app/                  # Cross-platform Flutter client
│   ├── pubspec.yaml              # Dart dependencies
│   └── lib/
│       ├── main.dart             # App entry point
│       ├── app.dart              # MaterialApp with routing
│       ├── core/                 # API client, constants, theme
│       ├── l10n/                 # Localization (5 languages)
│       ├── models/               # User, Lesson, Syllabus models
│       ├── services/             # Auth, API, DB, localization services
│       └── screens/              # 12 screens (login → dashboard → lessons → quiz)
│
├── web/                          # Lightweight web portal
│   ├── index.html                # Single-page app shell
│   ├── css/style.css             # Mobile-first responsive CSS
│   ├── js/
│   │   ├── auth.js               # Firebase Google Sign-In + JWT
│   │   ├── app.js                # Main app logic
│   │   ├── markdown.js           # Secure Markdown → HTML renderer
│   │   └── i18n.js               # Client-side internationalization
│   └── locales/                  # en, hi, kn, te, ta JSON files
│
└── tasks/                        # Development task tracking
```

---

## 🚀 Quick Start

> **Prerequisites:** Python 3.11+, Flutter 3.22+ (optional for Flutter client), Git

### 1. Clone & configure

```bash
git clone <repository-url>
cd smartsiksha
cp .env.example .env
# Edit .env — add your GROQ_API_KEY and SERPER_API_KEY
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The database auto-initializes and seeds 30 curricula on first boot. API docs are at **http://localhost:8001/docs**.

### 3. Run a client

**Web portal** — open `web/index.html` in a browser (via Live Server or any HTTP server on port 5500).

**Flutter (Windows desktop):**
```powershell
cd flutter_app
flutter pub get
$env:CL = "/FS"
flutter run -d windows
```

**Flutter (Chrome):**
```bash
cd flutter_app
flutter pub get
flutter run -d chrome --web-port 5500
```

> See [HOW_TO_RUN.md](HOW_TO_RUN.md) for detailed setup instructions, troubleshooting, and all run options.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | LLM model name (default: `llama-3.3-70b-versatile`) |
| `SERPER_API_KEY` | Yes | API key from [serper.dev](https://serper.dev) |
| `DATABASE_URL` | No | SQLAlchemy URL (default: local SQLite) |
| `FIREBASE_PROJECT_ID` | No | Firebase project ID for Google Sign-In |
| `JWT_SECRET_KEY` | Yes | Random secret for JWT signing — generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_EXPIRE_MINUTES` | No | Token lifetime in minutes (default: 60) |
| `DEBUG` | No | Enable dev-mode auth bypass (default: false) |
| `UNSPLASH_ACCESS_KEY` | No | Unsplash API key for lesson images |

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | — | Health check |
| `GET` | `/api/languages` | — | List supported languages |
| `POST` | `/api/auth/google` | — | Google Sign-In (Firebase ID token → JWT) |
| `GET` | `/api/auth/me` | JWT | Current user profile |
| `POST` | `/api/auth/onboarding` | JWT | Complete curriculum onboarding |
| `PATCH` | `/api/auth/profile` | JWT | Update profile fields |
| `POST` | `/api/ask` | JWT | Generate AI lesson (RAG pipeline) |
| `POST` | `/api/lessons/save` | JWT | Save a lesson |
| `GET` | `/api/lessons/mine` | JWT | Get current user's saved lessons |
| `GET` | `/api/syllabus/curricula` | — | List all 30 curricula |
| `GET` | `/api/syllabus/subjects` | — | Subjects for curriculum/class |
| `GET` | `/api/syllabus/chapters/{subject_id}` | — | Chapters for a subject |
| `POST` | `/api/quiz/generate` | JWT | Generate quiz for a chapter |
| `GET` | `/api/competitive/exams` | JWT | List competitive exams |
| `POST` | `/api/competitive/mock-test/generate` | JWT | Generate mock test |

Full interactive docs: **http://localhost:8001/docs**

---

## 🛡️ Security

- **Authentication:** Firebase Google Sign-In → backend-issued JWT (HS256, 60-min expiry)
- **Authorization:** All user-data endpoints enforce ownership checks
- **Rate limiting:** slowapi — 10 req/min for AI generation, 30 req/min default
- **Input validation:** Pydantic schemas on all request bodies
- **XSS protection:** Escape-first Markdown renderer, CSP headers on web portal
- **CORS:** Restricted to explicit localhost origins (no wildcards)
- **Secrets:** `.env` excluded via `.gitignore`, no defaults for critical keys

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI · Python 3.11 · SQLAlchemy (async) · Pydantic |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI / LLM** | Groq Cloud — Llama 3.3 70B Versatile |
| **Search** | Serper API (Google Search) |
| **Auth** | Firebase Authentication · python-jose JWT |
| **Flutter App** | Flutter 3.22+ · Dart · Provider · sqflite |
| **Web Portal** | Vanilla JS · Custom Markdown renderer · i18n |
| **Platforms** | Windows · Web · Android · iOS |

---

## 🌐 Supported Languages

| Code | Language | Script |
|------|----------|--------|
| `en` | English | Latin |
| `hi` | हिन्दी (Hindi) | Devanagari |
| `kn` | ಕನ್ನಡ (Kannada) | Kannada |
| `te` | తెలుగు (Telugu) | Telugu |
| `ta` | தமிழ் (Tamil) | Tamil |

All AI-generated content (lessons, quizzes, flashcards) is produced natively in the selected language. The UI is fully localized across all 5 languages for both the Flutter app and the web portal.

---

## 📄 License

This project was developed as part of an academic research initiative. See [Smart_Shiksha_IEEE_Paper.tex](Smart_Shiksha_IEEE_Paper.tex) for the accompanying IEEE paper.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure all API endpoints remain backward-compatible and include tests for new features.
