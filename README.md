# Worklog Manager

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.7.0-green.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](INSTALL.md)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A professional Python desktop application for precise work time tracking with automatic overtime calculation, break management, and comprehensive reporting capabilities. Built to ensure compliance with customizable work norms while providing detailed analytics and audit trails.

## Screenshot

![Worklog Manager Interface](images/worklog-manager-interface.png)

*Professional time tracking interface with real-time session monitoring, break management, and productivity analytics*

---

## Table of Contents

- [Worklog Manager](#worklog-manager)
  - [Screenshot](#screenshot)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Daily Workflow](#daily-workflow)
    - [Key Functions](#key-functions)
    - [Display Reference](#display-reference)
  - [Technical Architecture](#technical-architecture)
  - [Configuration](#configuration)
  - [Logging \& Monitoring](#logging--monitoring)
  - [Troubleshooting](#troubleshooting)
  - [Development Status](#development-status)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [Support](#support)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Key Features

- **Precise Time Tracking** - Real-time session tracking with 1-second accuracy and automatic productive time calculation
- **Break Management** - Support for multiple break types (Lunch, Coffee, General) with automatic duration tracking
- **Overtime Calculation** - Automatic detection and tracking against configurable work norms (default: 7.5 hours)
- **Action History & Revoke** - Undo up to 5 recent actions with full state restoration and validation
- **Export & Reporting** - Generate professional reports in CSV, JSON, or PDF formats with productivity analytics
- **Advanced UI** - Light/Dark themes, system tray integration, customizable keyboard shortcuts, and color-coded status indicators
- **Notification System** - Configurable alerts for work reminders, break times, and overtime warnings
- **Automated Backups** - Scheduled database backups with retention policies for data safety
- **Cross-Platform** - Compatible with Windows, macOS, and Linux

## Installation

**Requirements:** Python 3.7 or higher

**Quick Start:**
```bash
git clone <repository-url>
cd worklog-manager
python main.py
```

*Note: Uses Python standard library only - no external dependencies required for core functionality.*

## Usage

### Daily Workflow
1. **Start Day** - Begin time tracking for the current date
2. **Stop/Continue** - Pause for breaks (select type: Lunch, Coffee, or General) and resume work
3. **End Day** - Complete tracking and review summary (productive time, overtime, breaks)

### Key Functions

**Revoke Actions**
- Undo up to the last 5 actions with full state restoration
- Review action history before confirming rollback
- Safe validation prevents invalid state transitions

**Reset Day**
- Completely clear today's data and start fresh
- ⚠️ **Warning**: Permanently deletes all today's data - requires double confirmation

**Export Data**
- Quick export options: Today (CSV), This Week (JSON), or Custom (CSV/JSON/PDF)
- Professional reports include productivity metrics, break analysis, and statistical trends
- Automated file naming and organized export directory

### Display Reference

**Time Indicators:**
- Current Session • Total Work Time • Break Time • Productive Time • Remaining • Overtime

**Color Codes:**
- 🟢 Green: Meeting/exceeding targets
- 🟠 Orange: Approaching targets
- 🔴 Red: Overtime or critical status
- 🔵 Blue: Active session

## Technical Architecture

**Database:** SQLite with three core tables
- `work_sessions` - Daily work summaries and status
- `action_log` - Complete audit trail with timestamps
- `break_periods` - Individual break tracking by type

**Project Structure:**
```
worklog-manager/
├── main.py              # Application entry point
├── config.ini           # Configuration settings
├── gui/                 # UI components and dialogs
├── core/                # Business logic and calculations
├── data/                # Database operations and models
├── exporters/           # CSV, JSON, PDF export modules
├── logs/                # Daily log files
├── exports/             # Generated reports
└── backups/             # Automated database backups
```

## Configuration

Customize settings via `config.ini`:
- Work norm hours (default: 7.5)
- Theme and UI preferences
- Notification timing and alerts
- Backup retention policies
- Keyboard shortcuts

## Logging & Monitoring

Daily logs stored in `logs/` directory with format `worklog_YYYYMMDD.log`. Includes all actions, errors, and system events with configurable log levels.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Application won't start | Verify Python 3.7+ and file permissions |
| Database errors | Check disk space and write permissions |
| Timer not updating | Restart application or check system clock |
| Data not saving | Review logs and verify database file access |

**Debug:** Check `logs/worklog_YYYYMMDD.log` for detailed error information.

## Development Status

**Current Version: 1.7.0** - All phases completed
- ✅ Phase 1: Core time tracking and break management
- ✅ Phase 2: Action history and revoke system
- ✅ Phase 3: Export and reporting (CSV/JSON/PDF)
- ✅ Phase 4: Advanced features (themes, notifications, system tray, keyboard shortcuts)

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Installation Guide](INSTALL.md)** - Detailed setup instructions for all platforms
- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Packaging Guide](docs/packaging.md)** - Build standalone binaries with PyInstaller
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[Security Policy](SECURITY.md)** - Security considerations and reporting
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community guidelines

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- How to report bugs
- How to suggest features
- Development setup
- Code style guidelines
- Pull request process

## Support

- 📖 **Documentation**: Check the `docs/` directory
- 🐛 **Bug Reports**: [Open an issue](https://github.com/your-username/worklog-manager/issues/new?template=bug_report.md)
- 💡 **Feature Requests**: [Submit a request](https://github.com/your-username/worklog-manager/issues/new?template=feature_request.md)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/worklog-manager/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for credits and attributions.

---

<div align="center">

**Worklog Manager** - Professional time tracking for productive teams

⭐ Star this repository if you find it helpful!

[Report Bug](https://github.com/your-username/worklog-manager/issues) · [Request Feature](https://github.com/your-username/worklog-manager/issues) · [View Documentation](docs/)

</div>