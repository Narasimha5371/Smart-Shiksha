# Smart Shiksha — Flutter App

Cross-platform Flutter client for the Smart Shiksha AI-powered learning platform.

## Platforms

- **Windows** (desktop) — primary development target
- **Web** (Chrome) — via Flutter web
- **Android / iOS** — mobile builds

## Quick Start

```powershell
# Install dependencies
flutter pub get

# Run on Windows desktop
$env:CL = "/FS"
New-Item -ItemType Directory -Path "build\native_assets\windows" -Force | Out-Null
flutter run -d windows

# Run on Chrome
flutter run -d chrome --web-port 5500
```

## Architecture

- **State Management**: Provider (ChangeNotifier)
- **Auth**: Auth0 (Google OAuth) via backend JWT — dev-mode email login for desktop
- **Storage**: sqflite for offline lesson caching (desktop/mobile), no-op stub on web
- **Networking**: http package → FastAPI backend at `localhost:8001`
- **i18n**: Flutter ARB localization (English, Hindi, Kannada, Telugu, Tamil)

## Key Directories

| Path | Description |
|------|-------------|
| `lib/core/` | API client, constants, theme, platform checks |
| `lib/models/` | Dart data models |
| `lib/screens/` | All UI screens |
| `lib/services/` | Auth, API, and local DB services |
| `lib/l10n/` | Localization ARB files |

## Backend Requirement

The app requires the FastAPI backend running on port **8001**. See the root [HOW_TO_RUN.md](../HOW_TO_RUN.md) for setup instructions.
