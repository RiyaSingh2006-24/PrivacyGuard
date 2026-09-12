# PrivacyGuard

**Personal Digital Exposure & Home Network Security Monitor**

PrivacyGuard is a local-first security application that helps users understand what is visible on their home network and whether their email identity appears in known breach intelligence. It combines local network discovery, service exposure checks, device recognition, trusted-device tracking, identity exposure checks, persistent history, a transparent heuristic security score, and downloadable PDF reports in one dashboard.

> **Status:** active beta / portfolio project. Linux packaging has been tested in the development environment. Windows packaging scripts are included, but Windows should be treated as beta until tested on a clean Windows system.

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
- Windows build automation via `build_windows.bat`

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
**Packaging:** PyInstaller

## Project Structure

```text
PrivacyGuard/
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
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
└── .gitignore
```

## Development Setup

### 1. Backend

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

Install dependencies:

```bash
pip install -r requirements.txt
python start_backend.py
```

The API runs locally at:

```text
http://127.0.0.1:8000
```

### 2. Frontend development

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
npm run build
```

Copy the generated `dist` contents into `backend/web`, then package the backend with PyInstaller. The Linux development build uses `start_backend.py` as the entry point.

### Windows build

From Windows, run:

```text
backend\build_windows.bat
```

The script creates a Windows virtual environment, installs dependencies, builds the React frontend, and packages PrivacyGuard with PyInstaller.

## Security Model

PrivacyGuard intentionally limits network scanning to the automatically detected local network and rejects public network ranges. Scans are limited to a maximum of 256 addresses and only a controlled list of common service ports is checked.

An open port is treated as **service exposure**, not automatically as a vulnerability. The displayed security score is a transparent heuristic intended to summarize posture; it is **not CVSS, a penetration-test score, or a formal security certification**.

A device marked **Trusted** means only that the user recognizes it. It does not prove the device is secure.

## Privacy

- The security engine binds to `127.0.0.1` only.
- Scan history is stored locally in SQLite.
- Email values stored in history are masked.
- Local databases, generated reports, virtual environments, build output, and dependency folders are excluded from Git.
- Identity exposure checks require sending the entered email address to the external XposedOrNot breach-intelligence service for lookup.

## Limitations

- Ping-based discovery can miss devices that ignore ICMP.
- MAC resolution depends on the local neighbor/ARP cache and may be unavailable for some devices.
- Device type identification is intentionally conservative.
- The current service scanner checks a selected set of common TCP ports rather than performing a full vulnerability assessment.
- Windows support should remain labelled beta until verified on a clean Windows installation.

## Authorized Use

PrivacyGuard is intended only for networks and systems you own or have explicit permission to assess. Do not use it to scan third-party networks without authorization.

## Version

Current application version: **2.1.0**
