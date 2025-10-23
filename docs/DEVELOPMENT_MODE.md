# Development Mode - Auto-Reload Feature

## Overview

The Worklog Manager includes a development mode that automatically restarts the application whenever you make changes to any Python file. This eliminates the need to manually stop and restart the application during development.

## Quick Start

### 1. Install watchdog (one-time setup)

```bash
pip install watchdog
```

Or install all development dependencies:

```bash
pip install -r requirements.txt
```

### 2. Start in development mode

**Using Python directly:**
```bash
python dev_start.py
```

**Using convenience scripts:**

Windows:
```cmd
dev_start.bat
```

Linux/Mac:
```bash
./dev_start.sh
```

## Features

- **Automatic Restart**: Changes to any `.py` file trigger an automatic restart
- **Smart Watching**: Monitors `core/`, `gui/`, `utils/`, `exporters/` and root directory
- **Cooldown Protection**: Prevents multiple rapid restarts (1-second cooldown)
- **Graceful Shutdown**: Properly terminates the application before restart
- **Visual Feedback**: Clear console messages show what's happening

## Options

```bash
python dev_start.py              # Normal mode with file watching
python dev_start.py --verbose    # Show detailed file change events
python dev_start.py --no-watch   # Disable file watching
python dev_start.py --help       # Show help message
```

## What Gets Watched

The file watcher monitors these directories:
- Root directory (project files)
- `core/` - Business logic
- `gui/` - UI components
- `utils/` - Utility functions
- `exporters/` - Export modules

**Ignored directories:**
- `__pycache__/`
- `build/`
- `backups/`
- `logs/`
- `exports/`
- `.git/`

## How It Works

1. The `dev_start.py` script starts the main application as a subprocess
2. A file watcher (using `watchdog` library) monitors Python files for changes
3. When a change is detected:
   - The current application process is gracefully terminated
   - A brief pause (0.5s) allows cleanup
   - The application is automatically restarted
4. The cycle continues until you press `Ctrl+C`

## Troubleshooting

### watchdog not installed

```
ERROR: watchdog package not found!
Install it with: pip install watchdog
```

**Solution:** Run `pip install watchdog`

### Application doesn't restart on changes

**Possible causes:**
- File is in an ignored directory
- File extension is not `.py`
- Cooldown period active (wait 1 second between saves)

**Solution:** Check the console for file change messages with `--verbose` flag

### Application crashes on restart

The development mode will show the error in the console and wait for the next file change to restart. Check the logs for details.

## Best Practices

1. **Save your work**: Changes only trigger on file save
2. **Wait for restart**: Let the application fully restart before testing
3. **Check console**: Watch for restart messages and errors
4. **Use version control**: Commit working code before making changes

## Production Usage

**Don't use development mode in production!** 

For production deployment:
```bash
python main.py
# or
python start_worklog.py
```

## Tips

- Use `--verbose` to debug which files trigger restarts
- Press `Ctrl+C` to cleanly exit development mode
- The application state (database) persists across restarts
- Console messages use emojis for easy scanning:
  - 🚀 Application starting
  - ✓ Operation successful
  - 📝 File changed
  - 🔄 Restarting
  - ⚠️ Warning
  - ✗ Error

## Example Session

```
$ python dev_start.py
============================================================
Worklog Manager - Development Mode
============================================================
👀 File watcher enabled - application will auto-reload on changes
   Press Ctrl+C to stop
🚀 Starting Worklog Manager...
✓ Application started (PID: 12345)

[... make a change to gui/main_window.py ...]

📝 File changed: main_window.py
🔄 Restarting application...
⏹  Stopping application...
✓ Application stopped
🚀 Starting Worklog Manager...
✓ Application started (PID: 12346)
```

## Need Help?

- Check the main [README.md](README.md) for general documentation
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue if you encounter problems

---

Happy developing! 🚀
