# QA Automation Portfolio — Desktop Application E2E Testing

End-to-end test automation framework for a Windows desktop application (Chromium-based) with a web admin portal. Tests run across a fleet of 12 Windows VMs managed by GitLab CI/CD on a Proxmox hypervisor.

---

## What This Project Demonstrates

| Area | Details |
|---|---|
| **UI Test Automation** | Playwright (Python) with Page Object Model, pytest fixtures, parametrized tests |
| **Cross-System Verification** | Tests span the desktop app, web admin portal, SQLite databases, and REST API |
| **CI/CD Pipeline** | GitLab CI with parallel execution across 12 Windows VMs, automatic VM snapshot rollback, Allure reporting |
| **Infrastructure as Code** | Custom C# Windows Service for GitLab Runner lifecycle, Proxmox VM management scripts |
| **Desktop App Testing** | Silent installation, upgrade flows, process monitoring via pywinauto/subprocess |
| **Reporting** | Custom Allure integration with step-level granularity, failure artifact collection (logs, databases, HAR, screenshots, Event Viewer) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitLab CI/CD                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ prepare  │→ │   test   │→ │  upload  │→ │ report │  │
│  │(VM reset)│  │(parallel)│  │ (rsync)  │  │(Allure)│  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│       │          │ │ │ │                        │        │
│       ▼          ▼ ▼ ▼ ▼                        ▼        │
│  ┌─────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Proxmox │  │ Windows VM Fleet │  │  Allure Report  │ │
│  │  Host   │  │  (12 runners)    │  │     Server      │ │
│  └─────────┘  └──────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘

Each Windows VM:
┌──────────────────────────────────────────────────┐
│  GitLab Runner (C# Windows Service)              │
│  ├── Registers runner on start                   │
│  ├── Runs test jobs                              │
│  └── Unregisters on stop                         │
│                                                  │
│  Test Execution:                                 │
│  ├── Install desktop app (silent)                │
│  ├── Launch app via Scheduled Task               │
│  ├── Connect Playwright via CDP (port 9333)      │
│  ├── Run pytest suite                            │
│  ├── Export Allure results to SMB share          │
│  └── Collect failure artifacts                   │
└──────────────────────────────────────────────────┘
```

---

## Project Structure

```
qa-automation-portfolio/
├── tests/                          # All test modules
│   ├── conftest.py                 # Shared fixtures (browser, pages, allure config)
│   ├── ui/                         # Browser-based UI tests
│   │   ├── conftest.py             # UI fixtures (page objects, CDP connection)
│   │   ├── pages/                  # Page Object Model
│   │   │   ├── base_page.py        # Base page with common interactions
│   │   │   ├── activation_page.py  # App activation flow
│   │   │   ├── dashboard_page.py   # Main dashboard
│   │   │   ├── lesson_page.py      # Lesson viewer
│   │   │   ├── quiz_page.py        # Quiz/test taking
│   │   │   └── admin/              # Admin portal pages
│   │   │       ├── login_page.py
│   │   │       ├── questions_page.py
│   │   │       └── student_page.py
│   │   ├── test_smoke.py           # Full E2E smoke test (13 steps)
│   │   ├── test_activation.py      # Activation & login flows
│   │   ├── test_lesson_flow.py     # Lesson navigation & completion
│   │   ├── test_quiz.py            # Quiz answer & result verification
│   │   ├── test_progress_test.py   # Progress test with data-driven answers
│   │   └── test_admin_questions.py # Admin portal question type checks
│   ├── api/                        # API/endpoint verification tests
│   │   ├── conftest.py
│   │   └── test_student_data.py    # Tracking data, study time, test results
│   ├── database/                   # SQLite database structure tests
│   │   ├── conftest.py
│   │   └── test_schema.py          # Schema integrity, referential checks
│   └── desktop/                    # Native Windows desktop tests
│       ├── conftest.py
│       └── test_installation.py    # Install, upgrade, service management
│
├── framework/                      # Reusable test framework
│   ├── config.py                   # Centralized configuration
│   ├── browser.py                  # CDP browser connection management
│   ├── reporting/
│   │   ├── allure_helpers.py       # Custom Allure result builder
│   │   └── artifacts.py            # Failure artifact collector
│   ├── helpers/
│   │   ├── text.py                 # Text normalization utilities
│   │   └── waiters.py              # Polling/wait utilities
│   └── windows/
│       └── client.py               # Windows subprocess execution
│
├── infrastructure/                 # CI/CD & VM management
│   ├── gitlab-runner-service/      # C# Windows Service source
│   ├── pipeline/                   # VM lifecycle scripts
│   └── docs/                       # Infrastructure documentation
│
├── config/                         # Test data & environment config
│   ├── main.env.example
│   └── *.ini.example               # Example test data files
│
├── .gitlab-ci.yml                  # CI/CD pipeline definition
├── pyproject.toml                  # Python project config (pytest, tools)
└── requirements.txt                # Python dependencies
```

---

## Tech Stack

| Technology | Role |
|---|---|
| **Python 3.13** | Test language |
| **Playwright** | Browser automation (CDP connection to Chromium-based desktop app) |
| **pytest** | Test runner with fixtures, parametrization, markers |
| **Allure** | Test reporting with step-level detail and failure artifacts |
| **GitLab CI/CD** | Pipeline orchestration with parallel jobs |
| **Proxmox VE** | VM hypervisor for test fleet |
| **C# / .NET** | GitLab Runner Windows Service |
| **SQLite** | Application database verification |
| **pywinauto** | Native Windows UI automation (installer flows) |

---

## Key Features

### Page Object Model
Clean separation between test logic and page interactions. Each page class encapsulates selectors, actions, and assertions.

```python
class DashboardPage(BasePage):
    def select_module(self, module_name: str) -> None:
        self.page.select_option("select.module-selector", label=module_name)

    def open_lesson(self, lesson_id: str) -> "LessonPage":
        self.page.locator(self._lesson_selector(lesson_id)).click()
        return LessonPage(self.page)

    def wait_for_sync_ready(self) -> None:
        self.page.get_by_text(re.compile(r"Click to sync|Progress last saved")).wait_for(
            state="visible", timeout=60_000
        )
```

### Data-Driven Tests
Quiz answers loaded from configuration, enabling the same test to run against different question sets:

```python
@pytest.mark.parametrize("test_section", ["smoke_test", "full_quiz"])
def test_take_quiz(dashboard_page, question_bank, test_section):
    ...
```

### CI/CD Pipeline with VM Fleet
12 Windows VMs are snapshot-rolled-back before each run, ensuring a clean slate:

```yaml
test_job:
  parallel: 12
  tags: ["$[[ inputs.vm_group ]]"]
  script:
    - py -m pytest tests/ --alluredir=$EXPORT_PATH
```

### Failure Artifact Collection
On test failure, the framework automatically collects: Laravel logs, SQLite databases, temp folder archive, Windows Event Viewer export, HAR network recordings, and final screenshots.

---

## Running Tests

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Configure environment
cp config/main.env.example config/main.env
# Edit config/main.env with local values

# Open debug browser (leave running)
python -m framework.browser --debug

# Run all tests
pytest tests/

# Run specific test categories
pytest tests/ui/ -m smoke
pytest tests/database/
pytest tests/api/
```

### CI/CD

The pipeline is triggered on push to `main` or manually from GitLab UI. See [infrastructure/docs/pipeline.md](infrastructure/docs/pipeline.md) for full pipeline documentation.

---

## Test Coverage

| Suite | Tests | Scope |
|---|---|---|
| **Smoke** | 13 | Full E2E: account creation → activation → login → content download → lesson → quiz → sync → data verification |
| **Student Endpoints** | 15+ | Profile CRUD, course dates, test data, study time, module progress |
| **Question Types** | 6+ | Multi-select, annexes, answer images, wording edits, classification changes |
| **Database Schema** | 8+ | Syllabus/module table structure, NOT NULL constraints, referential integrity |
| **Installation** | 4 | Silent install, post-install config, service management, upgrade via updater |
| **Health Check** | 8 | Continuous loop: activate → lesson → quiz → sync → heartbeat ping |
