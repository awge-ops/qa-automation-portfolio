# GitLab Runner Windows Service

A C# Windows Service that manages the GitLab Runner lifecycle on test VMs.

## What It Does

**On service start:**
1. Ensures `C:\GitLab-Runner` directory exists
2. Reads the runner token from `C:\GitLab-Runner\token.txt`
3. Writes `config.toml` with runner configuration
4. Registers the runner with the GitLab instance
5. Starts the runner process
6. Downloads the latest GitLab Runner binary

**On service stop:**
1. Kills the runner process and all child processes
2. Unregisters the runner using the token

## Why a Custom Service?

GitLab Runner can run as a Windows Service natively, but this custom service adds:
- **Token-based config generation** — config.toml is written from a token file at startup, not stored in version control
- **Auto-registration** — the runner registers itself on start and unregisters on stop, keeping the GitLab instance clean
- **Binary auto-update** — downloads the latest runner binary on each start
- **Clean process management** — recursive process tree kill ensures no orphaned child processes

## Requirements

- Windows host with .NET Framework 4.7.2+
- Administrator permissions
- Network access to GitLab instance and S3 (for binary download)
- `C:\GitLab-Runner\token.txt` with the runner registration token
