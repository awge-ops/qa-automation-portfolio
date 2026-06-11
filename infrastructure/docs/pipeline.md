# Pipeline Documentation

## Overview

The CI/CD pipeline automates end-to-end testing across a fleet of Windows VMs hosted on a Proxmox hypervisor.

| Pipeline | Trigger | Purpose |
|---|---|---|
| **Test** | Push to `main` or manual trigger | Reset VMs → install app → run tests → collect results → publish Allure report |
| **Weekly Update** | Scheduled (`PIPELINE_TYPE=weekly_update`) | Boot VMs → install Windows Updates → snapshot → shut down |

## Architecture

```
GitLab CI/CD
├── prepare stage
│   ├── prepare_job (controller) ─── resetvms.sh → Proxmox API
│   └── report_cleanup_job (allure) ─── rm results
├── test stage
│   └── test_job ×12 (Windows VMs) ─── pytest → Allure JSON → SMB share
├── upload stage
│   └── upload_job (controller) ─── rsync → Allure server
├── report stage
│   └── generate_report_job (allure) ─── allure generate → web server
└── stop stage
    └── reset_job (controller) ─── stopvms.sh → Proxmox API
```

## Infrastructure

| Component | Role |
|---|---|
| **Proxmox host** | VM hypervisor — snapshot/rollback/start/stop via SSH |
| **Controller runner** | Linux server managing VM lifecycle and result transfer |
| **Windows VMs (×12)** | Test execution — each runs one parallel job instance |
| **Allure server** | Report generation and hosting |
| **SMB share** | Test result transport from VMs to controller |

## VM Lifecycle

### Reset (before each test run)
1. Rollback to latest Proxmox snapshot
2. Start VM
3. Wait for QEMU guest agent (up to 5 min)
4. Sync system clock (prevents TLS/token expiry failures)

### Weekly Update
1. Reset VMs to latest snapshot
2. Install Windows Updates via WUA COM API
3. Handle reboots with temporary autologon (DPAPI-encrypted password)
4. Snapshot updated state with VM memory
5. Clean up autologon credentials

## Test Results

```
Windows VMs → SMB share → rsync → Allure server → allure generate → web report
```

Each test produces Allure JSON with:
- Step-level pass/fail with timing
- Environment metadata (OS, language, timezone)
- Epic/feature/story labels
- Failure artifacts (logs, databases, HAR, screenshots, Event Viewer)

Results archived for 30 days, then auto-deleted.
