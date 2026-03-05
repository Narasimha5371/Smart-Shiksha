# Smart Shiksha — Flutter App

Cross-platform Flutter client for the Smart Shiksha AI-powered learning platform.

## Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **Windows** (desktop) | ✅ Primary | Requires Visual Studio 2022 with C++ workload |
| **Android** (emulator/device) | ✅ Supported | Uses `10.0.2.2:8001` for emulator → host connectivity |
| **Web** (Chrome) | ✅ Supported | No offline caching (sqflite uses no-op stub) |

> There is also a standalone **Material 3 web portal** in the `web/` directory at the project root — a vanilla JS SPA that mirrors the Flutter app's design.

## Quick Start

```powershell
# Install dependencies
flutter pub get

# Run on Windows desktop
$env:CL = "/FS"
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
flutter run -d windows

# Run on Android emulator
flutter emulators --launch Pixel_9_Pro_XL
Start-Sleep -Seconds 30
flutter run -d emulator-5554

# Run on Chrome
flutter run -d chrome --web-port 5500
```

## Architecture

- **State Management**: Provider (ChangeNotifier)
- **Auth**: Auth0 (Google OAuth) via backend JWT — dev-mode email login when `DEBUG=true`
- **Storage**: sqflite for offline lesson caching (desktop/mobile), no-op stub on web
- **Networking**: http package → FastAPI backend at `localhost:8001` (desktop/web) or `10.0.2.2:8001` (Android emulator)
- **i18n**: Flutter ARB localization (English, Hindi, Kannada, Telugu, Tamil)
- **Rendering**: Impeller (OpenGLES) on Android, default on Windows

## Screens (12 total)

| Screen | Description |
|--------|-------------|
| `login_screen.dart` | Email login (dev-mode) / Auth0 Google Sign-In |
| `onboarding_screen.dart` | Curriculum, class, stream, language selection |
| `dashboard_screen.dart` | 6-card grid: AI Tutor, Lessons, Quizzes, Revision, Exam Prep, Profile |
| `ai_tutor_screen.dart` | Conversational AI chat with suggestion chips |
| `lessons_browser_screen.dart` | Browse subjects → chapters → generate lessons |
| `lesson_screen.dart` | Full lesson view with Markdown rendering |
| `quiz_screen.dart` | MCQ, multi-select, and numerical questions |
| `exam_prep_screen.dart` | JEE/NEET/Board exam mock tests |
| `revision_screen.dart` | Flashcard decks for revision |
| `profile_screen.dart` | User settings: curriculum, language, stats |
| `settings_screen.dart` | App settings and preferences |
| `home_screen.dart` | Navigation shell |

## Key Directories

| Path | Description |
|------|-------------|
| `lib/core/` | API client, constants, theme, platform checks |
| `lib/models/` | Dart data models |
| `lib/screens/` | All 12 UI screens |
| `lib/services/` | Auth, API, and local DB services |
| `lib/l10n/` | Localization ARB files (5 languages) |
| `android/` | Android platform files (Manifest, Gradle) |
| `windows/` | Windows native runner |

## Backend Requirement

The app requires the FastAPI backend running on port **8001**. See the root [HOW_TO_RUN.md](../HOW_TO_RUN.md) for setup instructions.
