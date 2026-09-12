# PrivacyGuard

**Personal Digital Exposure & Home Network Security Monitor**

PrivacyGuard is a local-first security application that helps users understand what is visible on their home network and whether their email identity appears in known breach intelligence. It combines local network discovery, service exposure checks, device recognition, trusted-device tracking, identity exposure checks, persistent history, a transparent heuristic security score, and downloadable PDF reports in one dashboard.

> **Status:** active beta / portfolio project. Linux packaging has been tested in the development environment. Windows builds are now produced automatically on GitHub Actions and include a per-user installer, but the Windows release should remain labelled beta until the installer is manually verified on a clean Windows machine.

## Features

- Local network discovery on private networks only
- Common TCP service checks for selected ports
- Risk classification with user-facing recommendations
- Persistent known-device registry
- New-device detection across scans
- Trusted/recognized device controls
- Identity exposure checks using XposedOrNot breach intelligence
- Local SQLite history with masked identity values
- Dashboard security posture score
- Downloadable PDF security report
- FastAPI backend served only on `127.0.0.1`
- React/Vite frontend bundled into the local application
- Linux packaging with PyInstaller
- Windows packaging with PyInstaller + Inno Setup
- Automated Windows build and packaged-app health smoke test with GitHub Actions

## Architecture

```text
Browser UI (React)
        |
        | relative /api requests
        v
FastAPI Local Security Engine
        |
        +-- Network discovery / service checks
        +-- Device registry + trusted-device state
        +-- Identity exposure checker
        +-- SQLite local storage
        +-- PDF report generator
```

The production build serves both the React UI and API from the same local process at `http://127.0.0.1:8000`.

## Tech Stack

**Frontend:** React, Vite, React Router, Lucide React  
**Backend:** Python, FastAPI, Uvicorn, psutil, httpx  
**Storage:** SQLite  
**Reports:** ReportLab  
**Packaging:** PyInstaller, Inno Setup  
**CI:** GitHub Actions

## Project Structure

```text
PrivacyGuard/
├── .github/
│   └── workflows/
│       └── windows-release.yml
├── backend/
│   ├── main.py
│   ├── history_db.py
│   ├── trusted_api.py
│   ├── report_api.py
│   ├── storage.py
│   ├── frontend_host.py
│   ├── start_backend.py
│   ├── start_backend.sh
│   ├── build_windows.bat
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── installer/
│   └── PrivacyGuard.iss
├── PRIVACY.md
├── SECURITY.md
├── RELEASE_CHECKLIST.md
└── .gitignore
```

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```bat
venv\Scripts\activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python start_backend.py
```

The local application engine runs at:

```text
http://127.0.0.1:8000
```

### Frontend development

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests to the local FastAPI engine.

## Production Build

Build the React frontend:

```bash
cd frontend
npm install
npm run build
```

The production frontend is copied into `backend/web` before the application is packaged with PyInstaller.

### Windows build on a local Windows machine

Run:

```text
backend\build_windows.bat
```

The script prepares dependencies, builds the React frontend, and packages the application into `backend\dist\PrivacyGuard\`.

### Automated Windows build

The repository includes `.github/workflows/windows-release.yml`. On relevant pushes to `main`, GitHub Actions:

1. builds the React frontend on Windows,
2. creates `PrivacyGuard.exe` with PyInstaller,
3. starts the packaged executable and verifies `/api/health`,
4. creates `PrivacyGuard-Setup-2.1.0.exe` with Inno Setup,
5. uploads both the portable package and installer as workflow artifacts.

The installer uses a per-user install directory, so it does not require administrator privileges for the normal installation path.

## Security Model

PrivacyGuard intentionally limits network scanning to the automatically detected local network and rejects public network ranges. Scans are limited to a maximum of 256 addresses and only a controlled list of common service ports is checked.

An open port is treated as **service exposure**, not automatically as a vulnerability. The displayed security score is a transparent heuristic intended to summarize posture; it is **not CVSS, a penetration-test score, or a formal security certification**.

A device marked **Trusted** means only that the user recognizes it. It does not prove the device is secure.

## Privacy

- The security engine binds to `127.0.0.1` only.
- Scan history and trusted-device state are stored in a local SQLite database.
- Email values stored in local history are masked.
- On Windows, persistent application data is stored under the user's local application-data directory.
- Local databases, generated reports, virtual environments, dependency folders, and build output are excluded from Git.
- Identity exposure checks require sending the entered email address to the external XposedOrNot breach-intelligence service for lookup.

See [`PRIVACY.md`](PRIVACY.md) for additional privacy notes.

## Limitations

- Ping-based discovery can miss devices that ignore ICMP.
- MAC resolution depends on the local neighbor/ARP cache and may be unavailable for some devices.
- Device type identification is intentionally conservative.
- The current service scanner checks a selected set of common TCP ports rather than performing a full vulnerability assessment.
- Windows support remains beta until the installer completes the manual checks in [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md).
- The current Windows build is unsigned, so SmartScreen may display an unknown-publisher warning.

## Authorized Use

PrivacyGuard is intended only for networks and systems you own or have explicit permission to assess. Do not use it to scan third-party networks without authorization.

## Version

Current application version: **2.1.0**
