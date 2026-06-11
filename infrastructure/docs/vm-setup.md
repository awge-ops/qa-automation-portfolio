# Test VM Setup Guide

## Overview

The test infrastructure runs on **Proxmox VE** hypervisor managing 12 Windows VMs for parallel test execution. Each VM runs a GitLab Runner as a Windows Service and executes one test job at a time.

## VM Specifications

| Component | Specification |
|-----------|--------------|
| OS | Windows 10/11 Pro |
| vCPU | 2 cores |
| RAM | 4 GB |
| Disk | 60 GB (thin provisioned) |
| Network | Bridge to internal VLAN |

## Setup Steps

### 1. Base Windows Installation

1. Create VM in Proxmox with specs above
2. Install Windows from ISO
3. Enable RDP and WinRM for remote management
4. Disable Windows Update (managed manually)
5. Set static IP within the test VLAN range

### 2. Runtime Dependencies

```powershell
# Install .NET Framework 4.7.2+ (usually present)
# Install PowerShell 7
winget install Microsoft.PowerShell

# Create runner directory
New-Item -ItemType Directory -Path "C:\GitLab-Runner" -Force
```

### 3. Application Under Test

```powershell
# Install the desktop application silently
Start-Process -FilePath ".\app-installer.exe" -ArgumentList "/S" -Wait

# Verify installation
Test-Path "C:\Program Files (x86)\AppUnderTest\app.exe"
```

### 4. GitLab Runner Service

1. Place the runner registration token in `C:\GitLab-Runner\token.txt`
2. Install the custom Windows Service (see [RunnerService](../gitlab-runner-service/README.md))
3. The service handles runner binary download, registration, and lifecycle

```powershell
# Install the service
sc.exe create GitLabRunnerService binPath= "C:\GitLab-Runner\RunnerService.exe"
sc.exe config GitLabRunnerService start= auto
sc.exe start GitLabRunnerService
```

### 5. Chrome Remote Debugging

The application under test uses an embedded Chromium browser. Tests connect via CDP:

```powershell
# Configure the app to launch with remote debugging
# (Application-specific configuration step)
# Tests connect to: http://127.0.0.1:9333
```

### 6. Create Clean Snapshot

Once the VM is fully configured and verified:

```bash
# From the Proxmox host or via API
./snapshotvms.sh clean-state "Base setup with app installed"
```

## Snapshot Strategy

| Snapshot | Purpose | When Created |
|----------|---------|--------------|
| `clean-state` | Fresh install, no test data | After initial setup |
| `post-update` | After weekly app update | Weekly pipeline |

The CI pipeline rolls back to `clean-state` before each test run, ensuring deterministic test execution regardless of previous test outcomes.

## Network Layout

```
┌─────────────────────────────────────────┐
│              Proxmox VE Host            │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ VM-100  │ │ VM-101  │ │  ...    │   │
│  │ Runner  │ │ Runner  │ │ Runner  │   │
│  │ :9333   │ │ :9333   │ │ :9333   │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
│       └───────────┼───────────┘         │
│              Internal VLAN              │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │   GitLab    │
        │   Server    │
        └─────────────┘
```

## Maintenance

- **Weekly**: Application update pipeline runs automatically, creates `post-update` snapshot
- **Monthly**: Windows security patches (manual, then new `clean-state` snapshot)
- **As needed**: Proxmox host updates, runner binary updates (handled by service)
