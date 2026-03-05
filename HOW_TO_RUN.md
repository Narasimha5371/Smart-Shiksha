# Smart Shiksha — How to Run

A step-by-step guide to set up and run the Smart Shiksha platform (FastAPI backend + Flutter frontend).

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11+ | <https://www.python.org/downloads/> |
| **Flutter** | 3.22+ | <https://docs.flutter.dev/get-started/install> |
| **Visual Studio 2022** | (with C++ desktop workload) | <https://visualstudio.microsoft.com/> — required for Windows desktop builds |
| **Git** | Any recent version | <https://git-scm.com/downloads> |
| **Chrome** | Latest | For running the web version |

> **Windows users**: Make sure `python`, `flutter`, and `git` are available in your PATH.

---

## Project Structure

```
smartsiksha/
├── .env                      # API keys & config (backend reads this)
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # SQLAlchemy async engine
│   │   ├── models.py         # ORM models (10 tables)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── auth.py           # JWT + Auth0 auth (JWKS/RS256)
│   │   ├── routers/          # API route handlers
│   │   └── services/         # AI generation, syllabus seeding
│   ├── requirements.txt
│   └── smartsiksha.db        # SQLite database (auto-created)
├── flutter_app/
│   ├── lib/                  # Dart source code
│   ├── windows/              # Windows-specific native code
│   ├── web/                  # Web-specific assets
│   ├── pubspec.yaml          # Flutter dependencies
│   └── Directory.Build.props # MSBuild fix for PDB race conditions
└── Smart_Shiksha_IEEE_Paper.tex
```

---

## Step 1 — Configure Environment Variables

The project ships with a `.env` file at the repository root. Open it and fill in your API keys:

```dotenv
# Required — Groq LLM (get free key at https://console.groq.com)
GROQ_API_KEY="your-groq-api-key"
GROQ_MODEL="llama-3.3-70b-versatile"

# Required — Serper Google Search API (get key at https://serper.dev)
SERPER_API_KEY="your-serper-api-key"

# Database (default is local SQLite — no setup needed)
DATABASE_URL="sqlite+aiosqlite:///./smartsiksha.db"
DEBUG=false

# Auth0 (Authentication — get credentials at https://auth0.com)
AUTH0_DOMAIN="your-auth0-domain.us.auth0.com"
AUTH0_CLIENT_ID="your-auth0-client-id"
JWT_SECRET_KEY="change-me-to-a-random-secret-in-production"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=10080

# Optional — Unsplash images for lessons
UNSPLASH_ACCESS_KEY=""
```

> **Note**: Without `GROQ_API_KEY` and `SERPER_API_KEY`, AI features (lesson generation, quizzes, mock tests) will not work. All other features (syllabus browsing, profile, progress) work without them.

---

## Step 2 — Set Up the Backend

### 2.1 Install Python Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2.2 Initialize the Database

This creates the SQLite database and seeds it with 1,311 subjects and 17,038 chapters across 30 Indian curricula:

```powershell
cd backend
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db()); print('DB created')"
```

> **To reset the database** (start fresh):
> ```powershell
> cd backend
> Remove-Item -Force smartsiksha.db -ErrorAction SilentlyContinue
> python -c "import asyncio; from app.database import init_db; asyncio.run(init_db()); print('DB recreated')"
> ```

### 2.3 Start the Backend Server

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     🚀 Starting Smart Shiksha backend…
INFO:     ✅ Database tables ensured.
```

### 2.4 Verify the Backend

Open your browser and visit:

- **Swagger UI**: <http://localhost:8001/docs> — interactive API documentation
- **Health check**: <http://localhost:8001/api/health> — should return `{"status": "healthy"}`

> **Port 8001**: The backend runs on port **8001** (not 8000). The Flutter app is preconfigured to connect to `http://localhost:8001/api`.

> **If port 8001 is already in use**, free it first:
> ```powershell
> Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
>   ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
> Start-Sleep 2
> ```

---

## Step 3 — Run the Flutter App

### Option A: Windows Desktop (Recommended)

**Prerequisites**: Visual Studio 2022 with "Desktop development with C++" workload installed.

```powershell
cd flutter_app

# Set compiler flag to avoid PDB race conditions
$env:CL = "/FS"

# Ensure native_assets directory exists
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null

# Get dependencies
flutter pub get

# Run in debug mode
flutter run -d windows
```

> **First build** takes 3–5 minutes (compiles SQLite native libraries). Subsequent builds are much faster.

> **If you get MSB8066 / PDB errors**, run:
> ```powershell
> flutter clean
> flutter pub get
> $env:CL = "/FS"
> New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
> flutter run -d windows
> ```

### Option B: Web (Chrome)

```powershell
cd flutter_app
flutter pub get
flutter run -d chrome --web-port 5500
```

This opens the app in Chrome at `http://localhost:5500`.

> **Note**: Local SQLite caching (offline revision) is not available on the web platform — it uses a no-op stub instead. All other features work normally.

### Option C: Build Release Executable (Windows)

```powershell
cd flutter_app
$env:CL = "/FS"
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
flutter build windows --release
```

The standalone `.exe` is generated at:

```
flutter_app\build\windows\x64\runner\Release\smart_shiksha.exe
```

Run it directly:

```powershell
Start-Process "flutter_app\build\windows\x64\runner\Release\smart_shiksha.exe"
```

### Option D: Android (Emulator or Physical Device)

**Prerequisites**: Android SDK, an Android emulator (e.g., Pixel 9 Pro XL) or a connected physical device.

```powershell
cd flutter_app
flutter pub get

# List available emulators
flutter emulators

# Launch an emulator (example: Pixel_9_Pro_XL)
flutter emulators --launch Pixel_9_Pro_XL

# Wait ~30 seconds for the emulator to boot, then:
flutter run -d emulator-5554
```

> **First build** takes 10–20 minutes (downloads NDK, Android SDK Platform, CMake, and all Gradle dependencies). Subsequent builds take under a minute.

> **Network configuration**: The Android emulator uses `10.0.2.2` to reach the host machine's `localhost`. This is pre-configured in `lib/core/constants.dart`. Internet permission and cleartext traffic (`android:usesCleartextTraffic="true"`) are already set in `AndroidManifest.xml`.

> **To find your device ID**:
> ```powershell
> flutter devices
> ```

---

## Step 4 — Run the Web Portal

The web portal is a standalone Material 3 SPA (vanilla JS) that mirrors the Flutter app's design. It provides login, a 6-card dashboard, AI tutor chat, saved lessons, and dark mode.

```powershell
cd web
python -m http.server 5500
```

Open **http://localhost:5500** in your browser. The portal connects to the same backend at `http://localhost:8001/api`.

> **Dev-mode login**: When `DEBUG=true` in `.env`, enter any name and email on the login screen to sign in without Auth0.

---

## Step 5 — Using the App

### First-Time Setup (Onboarding)

1. **Sign In**: Use Google Sign-In (production) or the dev-mode email login (when `DEBUG=true`).
2. **Select Curriculum**: Choose from 30 boards (CBSE, ICSE, AP Board, Karnataka Board, etc.).
3. **Select Class**: Pick a grade from 8 to 12.
4. **Select Stream** *(classes 11–12 only)*: Science, Commerce, or Arts.
5. **Select Language**: English, Hindi, Kannada, Telugu, or Tamil.

### Features

| Feature | Description |
|---------|-------------|
| **Lessons** | Browse subjects → chapters → generate AI lessons with RAG |
| **Quizzes** | 15 questions per chapter (7 MCQ + 4 MSQ + 4 Numerical) |
| **AI Tutor** | Chat with the AI about any academic topic |
| **Revision** | Review previously cached lessons offline |
| **Exam Prep** | Mock tests for JEE Mains, JEE Advanced, NEET, Board Exams |
| **Profile** | Change curriculum, class, stream, language; view stats |

---

## Quick-Start Commands (Copy-Paste)

Open **three terminals** and run:

**Terminal 1 — Backend:**
```powershell
cd backend
pip install -r requirements.txt
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Terminal 2 — Flutter (Windows):**
```powershell
cd flutter_app
flutter pub get
$env:CL = "/FS"
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
flutter run -d windows
```

**Terminal 2 — Flutter (Android, alternative):**
```powershell
cd flutter_app
flutter pub get
flutter emulators --launch Pixel_9_Pro_XL
Start-Sleep -Seconds 30
flutter run -d emulator-5554
```

**Terminal 3 — Web Portal:**
```powershell
cd web
python -m http.server 5500
# Open http://localhost:5500
```

---

## Troubleshooting

### Backend won't start — port in use

```powershell
# Find and kill the process using port 8001
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Start-Sleep 2
# Retry
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Flutter build fails with MSB8066 / PDB errors

```powershell
cd flutter_app
flutter clean
flutter pub get
$env:CL = "/FS"
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
flutter run -d windows
```

### `native_assets` directory missing

```powershell
New-Item -ItemType Directory -Path "flutter_app\build\native_assets\windows" -Force | Out-Null
```

### SQLite download fails during Flutter build

If the build fails while downloading SQLite source, retry — it's usually a network timeout. If persistent, manually place the SQLite tarball in:

```
flutter_app\build\windows\x64\_deps\sqlite3-subbuild\sqlite3-populate-prefix\src\
```

### AI features return errors

- Verify `GROQ_API_KEY` and `SERPER_API_KEY` are set correctly in the root `.env` file.
- Check your API quota at <https://console.groq.com> and <https://serper.dev>.
- The backend logs detailed errors — check the terminal running uvicorn.

### App can't connect to backend

- Ensure the backend is running on **port 8001** (check terminal output).
- The Flutter app expects the backend at `http://localhost:8001/api` for desktop.
- For Android emulators, it uses `http://10.0.2.2:8001/api` (auto-configured).
- The web portal connects to `http://localhost:8001/api`.

### Android first build is very slow

The first Gradle build downloads NDK, Android SDK Platform 35, CMake 3.22.1, and all Gradle dependencies. This can take 10–20 minutes. Subsequent builds use cached artifacts and complete in under a minute.

### Android emulator not detected

```powershell
# List emulators
flutter emulators
# Launch one
flutter emulators --launch <emulator-name>
# Wait for boot, then check
flutter devices
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/languages` | List supported languages |
| POST | `/api/auth/login` | Auth0 ID token → JWT login |
| POST | `/api/auth/google` | Backward-compat alias for /login |
| POST | `/api/auth/onboarding` | Complete curriculum onboarding |
| GET | `/api/auth/me` | Get current user profile |
| PATCH | `/api/auth/profile` | Update profile fields |
| POST | `/api/ask` | Generate AI lesson (RAG pipeline) |
| POST | `/api/lessons/save` | Save a lesson |
| GET | `/api/lessons/mine` | Get user’s saved lessons |
| GET | `/api/syllabus/curricula` | List all 30 curricula |
| GET | `/api/syllabus/subjects` | List subjects for a curriculum/class |
| GET | `/api/syllabus/chapters/{subject_id}` | List chapters for a subject |
| POST | `/api/quiz/generate` | Generate quiz questions |
| GET | `/api/quiz/questions/{chapter_id}` | Get existing quiz questions |
| POST | `/api/competitive/mock-test/generate` | Generate competitive exam mock test |
| GET | `/api/competitive/exams` | List competitive exams |
| GET | `/api/progress/` | Get user progress |

Full interactive docs available at **http://localhost:8001/docs** when the backend is running.

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python 3.11) |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy Async |
| LLM | Groq Cloud — Llama 3.3 70B Versatile |
| Web Search | Serper API (Google Search) |
| Auth | Auth0 (JWKS/RS256) + JWT (HS256) + dev-mode email login |
| Flutter App | Flutter 3.22+ (Dart) · Provider · sqflite |
| Web Portal | Material 3 SPA · Vanilla JS · Dark mode · i18n |
| Platforms | Windows · Android · Web Portal |
