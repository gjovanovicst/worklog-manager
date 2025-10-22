# Installation Guide

This guide provides detailed instructions for installing and setting up Worklog Manager on different operating systems.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## System Requirements

### Minimum Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows 7+, macOS 10.12+, or Linux (any modern distribution)
- **RAM**: 256 MB
- **Disk Space**: 50 MB (plus space for your data)
- **Display**: 1024x768 resolution or higher

### Recommended Requirements
- **Python**: 3.9 or higher
- **RAM**: 512 MB or more
- **Disk Space**: 100 MB or more

### Dependencies
Worklog Manager uses only Python standard library modules:
- `tkinter` - GUI framework (included with Python)
- `sqlite3` - Database (included with Python)
- `datetime`, `json`, `configparser` - Standard library modules

**Optional Dependencies:**
- `reportlab` - Required only for PDF export functionality
  ```bash
  pip install reportlab
  ```

## Installation Methods

### Method 1: Download Release (Recommended)

1. Go to the [Releases](https://github.com/your-username/worklog-manager/releases) page
2. Download the latest release ZIP file
3. Extract to your desired location
4. Run the application

### Method 2: Clone from Git

```bash
# Clone the repository
git clone https://github.com/your-username/worklog-manager.git

# Navigate to the directory
cd worklog-manager

# Run the application
python main.py
```

### Method 3: Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/your-username/worklog-manager.git
cd worklog-manager

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install development dependencies (if any)
pip install -r requirements.txt

# Run the application
python main.py
```

## Platform-Specific Instructions

### Windows

#### Prerequisites
1. **Install Python**
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
   - Verify installation:
     ```cmd
     python --version
     ```

#### Installation
1. Download or clone the repository
2. Double-click `start_worklog.bat` or run:
   ```cmd
   python main.py
   ```

#### Creating a Desktop Shortcut
1. Right-click on `start_worklog.bat`
2. Select "Create shortcut"
3. Move shortcut to Desktop
4. (Optional) Right-click shortcut → Properties → Change Icon

### macOS

#### Prerequisites
1. **Install Python** (if not already installed)
   ```bash
   # Check if Python 3 is installed
   python3 --version
   
   # If not installed, use Homebrew
   brew install python3
   ```

#### Installation
1. Download or clone the repository
2. Make the startup script executable:
   ```bash
   chmod +x start_worklog.sh
   ```
3. Run the application:
   ```bash
   python3 main.py
   # or
   ./start_worklog.sh
   ```

#### Creating an Application Launcher
Create a file `Worklog Manager.app` using Automator or create an alias to `start_worklog.sh`.

### Linux

#### Prerequisites
1. **Install Python and Tkinter**
   ```bash
   # Debian/Ubuntu
   sudo apt-get update
   sudo apt-get install python3 python3-tk
   
   # Fedora
   sudo dnf install python3 python3-tkinter
   
   # Arch Linux
   sudo pacman -S python tk
   ```

#### Installation
1. Download or clone the repository
2. Make the startup script executable:
   ```bash
   chmod +x start_worklog.sh
   ```
3. Run the application:
   ```bash
   python3 main.py
   # or
   ./start_worklog.sh
   ```

#### Creating a Desktop Entry
Create a file `~/.local/share/applications/worklog-manager.desktop`:
```desktop
[Desktop Entry]
Type=Application
Name=Worklog Manager
Comment=Professional time tracking application
Exec=/path/to/worklog-manager/start_worklog.sh
Path=/path/to/worklog-manager
Icon=/path/to/worklog-manager/icon.png
Terminal=false
Categories=Office;Utility;
```

## Verification

After installation, verify that Worklog Manager is working correctly:

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Check the main window appears** with:
   - Timer display showing "00:00:00"
   - Status showing "Not Started"
   - All control buttons visible

3. **Test basic functionality**
   - Click "Start Day" - timer should begin
   - Click "Stop" - status should change to "On Break"
   - Click "Continue" - status should return to "Working"

4. **Verify data persistence**
   - Close and reopen the application
   - Check that data is preserved

5. **Check log files**
   - Verify `logs/` directory is created
   - Check for today's log file

## Troubleshooting

### Python Not Found

**Symptoms**: `python: command not found` or `python3: command not found`

**Solution**:
- Verify Python is installed: `python --version` or `python3 --version`
- On Windows, add Python to PATH
- On macOS/Linux, use `python3` instead of `python`

### Tkinter Not Available

**Symptoms**: `ImportError: No module named 'tkinter'`

**Solution**:
```bash
# Windows: Reinstall Python with tcl/tk support
# Download installer from python.org and ensure tcl/tk is selected

# macOS:
brew install python-tk

# Linux (Debian/Ubuntu):
sudo apt-get install python3-tk

# Linux (Fedora):
sudo dnf install python3-tkinter
```

### Permission Denied

**Symptoms**: `PermissionError` when running the application

**Solution**:
```bash
# Make script executable (macOS/Linux)
chmod +x start_worklog.sh

# Or run with python directly
python main.py
```

### Database Locked Error

**Symptoms**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close any other instances of the application
- Check if another process is accessing the database
- Restart the application

### GUI Not Displaying Correctly

**Symptoms**: Windows appear blank or buttons are missing

**Solution**:
- Update Python to the latest version
- Try running with different theme settings
- Check display scaling settings (Windows)

## Configuration

### First Run Setup

On first run, Worklog Manager will:
1. Create the database file (`worklog.db`)
2. Create necessary directories (`logs/`, `exports/`, `backups/`)
3. Generate default configuration file (`config.ini`)
4. Create settings file (`settings.json`)

### Customization

Edit `config.ini` to customize:
```ini
[WorkNorm]
hours = 7.5

[UI]
theme = light

[Notifications]
enabled = true

[Backup]
retention_days = 30
```

See [Configuration Guide](docs/CONFIGURATION.md) for detailed options.

## Next Steps

After successful installation:

1. **Read the [Quick Start Guide](QUICKSTART.md)** to learn basic usage
2. **Review [README.md](README.md)** for feature overview
3. **Configure settings** to match your preferences
4. **Start tracking** your work time!

## Building Installers

Ready to ship Worklog Manager to other users? Follow the
[Packaging Guide](docs/packaging.md) to generate PyInstaller builds for Windows,
macOS, and Linux. The guide walks through prerequisites, build commands, and
next steps for wrapping the binaries in native installers.

## Updating

To update to the latest version:

### From Git
```bash
cd worklog-manager
git pull origin main
python main.py
```

### From Release
1. Download the latest release
2. Backup your data (`worklog.db`, `config.ini`, `settings.json`)
3. Extract new version
4. Copy your backup files to the new installation
5. Run the application

**Note**: Always backup your data before updating!

## Uninstalling

To remove Worklog Manager:

1. **Backup your data** (if you want to keep it)
   - Copy `worklog.db`
   - Copy `exports/` directory
   - Copy any configuration files

2. **Delete the application directory**
   ```bash
   # The entire worklog-manager folder
   rm -rf worklog-manager
   ```

3. **Remove desktop shortcuts** (if created)

Your data will be permanently deleted unless backed up.

## Getting Help

If you encounter issues during installation:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review [existing issues](https://github.com/your-username/worklog-manager/issues)
3. Create a [new issue](https://github.com/your-username/worklog-manager/issues/new) with:
   - Your operating system and version
   - Python version (`python --version`)
   - Error messages
   - Steps to reproduce

## Support

- **Documentation**: See the `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/your-username/worklog-manager/issues)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Happy tracking!** 🎉
