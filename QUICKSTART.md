# Worklog Manager - Quick Start Guide

## 🚀 Getting Started

### 1. Launch the Application

**Normal Mode:**
```bash
cd c:\work\worklog-manager
python main.py
```

**Development Mode (with auto-reload):**
```bash
# Install watchdog first (one time only)
pip install watchdog

# Then start in development mode
python dev_start.py

# Or use the convenience scripts:
# Windows:
dev_start.bat

# Linux/Mac:
./dev_start.sh
```

The development mode will automatically restart the application whenever you change any Python file in the project. This is useful when developing or customizing the application.

### 2. Start Your Work Day
1. Click **"Start Day"** button
2. Timer begins tracking your work time
3. Status changes to "Working"

### 3. Take Breaks
1. Select break type: **Lunch**, **Coffee**, or **General**
2. Click **"Stop"** when leaving your workspace
3. Status changes to "On Break"
4. Click **"Continue"** when returning
5. Status returns to "Working"

### 4. Monitor Your Progress
Watch the **Time Summary** panel for real-time updates:
- **Current Session**: Active work time
- **Total Work Time**: All work periods combined
- **Productive Time**: Your progress toward 7.5-hour goal
- **Remaining**: Time left to complete your work day
- **Overtime**: Time beyond the 7.5-hour target

### 5. End Your Day
1. Click **"End Day"** when finished
2. Review the summary of your work time
3. Confirm to save the day's data
4. Status changes to "Day Ended"

## 📊 Understanding the Interface

### Color Indicators
- **🟢 Green**: Meeting targets, good progress
- **🟠 Orange**: Approaching targets, warnings  
- **🔴 Red**: Overtime or critical status
- **🔵 Blue**: Current active session

### Button States
- **Enabled**: Action is available in current state
- **Disabled**: Action not allowed (prevents errors)

### Break Types
- **Lunch**: Formal meal breaks
- **Coffee**: Short refreshment breaks
- **General**: Any other interruption

## 💾 Data Storage

- **Database**: `worklog.db` (SQLite)
- **Logs**: `logs/worklog_YYYYMMDD.log`
- **Config**: `config.ini`
- **Exports**: `exports/` (coming soon)

## 🔧 Configuration

Edit `config.ini` to customize:
- Work norm hours (default: 7.5)
- Timer update frequency
- Colors and themes
- Backup settings

## ❓ Need Help?

1. Check `README.md` for detailed documentation
2. Review `logs/` for error information
3. See `docs/` for technical specifications

---

**Happy time tracking! 🕐**