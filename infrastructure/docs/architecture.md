# Architecture

## System Under Test

The application under test is a Windows desktop application built on Chromium (Electron-style) with:
- **Frontend**: Vue.js SPA served via embedded web server
- **Backend**: PHP/Laravel running locally on `http://127.0.0.1:8888`
- **Database**: SQLite for local data storage
- **Admin Portal**: Web application for managing students, questions, and content

## Test Architecture

### Browser Automation
Tests connect to the desktop app's Chromium instance via **Chrome DevTools Protocol (CDP)** on port 9333. This allows Playwright to control the actual application, not a separate browser window.

```
Playwright ──CDP──► Chromium (port 9333) ──HTTP──► Laravel (port 8888) ──SQL──► SQLite
```

### Test Layers

| Layer | Tool | Scope |
|---|---|---|
| UI (App) | Playwright + POM | Student flows: activation, lessons, quizzes |
| UI (Admin) | Playwright + POM | Admin flows: student management, question verification |
| API/Data | Playwright (admin portal) | Cross-system data verification |
| Database | sqlite3 | Schema integrity, referential checks |
| Desktop | subprocess + pywinauto | Installation, upgrade, service management |

### Reporting
Custom Allure integration provides:
- Step-level granularity with timing
- Automatic failure artifact collection
- HAR network recording per test
- Environment labeling (OS version, language, timezone)

### CI/CD
GitLab CI with parallel execution across 12 Windows VMs:
- VMs managed via Proxmox API (snapshot/rollback/start/stop)
- Custom C# Windows Service for GitLab Runner lifecycle
- Weekly automated Windows Update pipeline to prevent update interference
