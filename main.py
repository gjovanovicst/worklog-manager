"""
Worklog Manager - Advanced Daily Work Time Tracking Application

A comprehensive Python GUI application for tracking daily work hours with advanced
features including automatic calculation of productive time, breaks, overtime,
theme management, notifications, backups, and system integration.

Core Features:
- Start/Stop/Continue work sessions
- Break type management (Lunch, Coffee, General)
- Real-time time calculations
- 7.5-hour work norm compliance
- SQLite database storage
- Detailed action logging
- Export functionality (CSV, JSON, PDF)
- Revoke/Undo system

Advanced Features (Phase 4):
- Settings management with persistent configuration
- Theme system (light/dark modes with custom colors)
- Notification system with work reminders and alerts
- Automatic backup system with scheduling
- Keyboard shortcuts (customizable)
- System tray integration
- Comprehensive help system
- Cross-platform compatibility

Author: GitHub Copilot
Version: 1.7.0
"""

import sys
import os
import json
import logging
import atexit
import configparser
import tempfile
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from scripts.packaging.create_shortcuts import create_shortcut, shortcut_exists
except ImportError:  # pragma: no cover - optional at runtime
    create_shortcut = None  # type: ignore[assignment]
    shortcut_exists = None  # type: ignore[assignment]

# Import datetime compatibility for Python 3.6 support (must be imported early)
from utils.datetime_compat import datetime_fromisoformat, fromisoformat_compat  # noqa: F401

# Import core application components
from gui.main_window import MainWindow
from core.settings import SettingsManager
from core.notification_manager import NotificationManager
from core.simple_backup_manager import BackupManager
from gui.theme_manager import ThemeManager
from gui.system_tray import SystemTrayManager
from gui.keyboard_shortcuts import KeyboardShortcutManager
from utils.single_instance import SingleInstanceManager

APP_SHORTCUT_NAME = "WorklogManager"
APP_VERSION = "1.7.0"
_SHORTCUT_DECISION_TTL = timedelta(days=30)
_SHORTCUT_STATE_FILE = Path.home() / ".worklog_manager" / "shortcut_prompt.json"


def _load_shortcut_state() -> dict:
    if not _SHORTCUT_STATE_FILE.exists():
        return {}
    try:
        return json.loads(_SHORTCUT_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_shortcut_state(state: dict) -> None:
    _SHORTCUT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SHORTCUT_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def _runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(project_root)


def _coerce_log_directory(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate


def _config_log_directory(base_dir: Path) -> Optional[Path]:
    config_path = base_dir / "config.ini"
    if not config_path.exists():
        return None

    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
    except Exception:
        return None

    if parser.has_option("Logging", "log_directory"):
        raw_value = parser.get("Logging", "log_directory").strip()
        if raw_value:
            return _coerce_log_directory(raw_value, base_dir)
    return None


def _prepare_log_directory(base_dir: Path) -> Tuple[Path, List[str]]:
    warnings: List[str] = []

    env_override = os.environ.get("WORKLOG_LOG_DIR", "").strip()
    if env_override:
        candidate = _coerce_log_directory(env_override, base_dir)
    else:
        candidate = _config_log_directory(base_dir) or (base_dir / "logs")

    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate, warnings
    except Exception as exc:
        warnings.append(
            f"Could not use log directory {candidate}: {exc}. Falling back to user log directory."
        )

    fallback = Path.home() / ".worklog_manager" / "logs"
    try:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback, warnings
    except Exception as exc:
        warnings.append(
            f"Could not create fallback log directory {fallback}: {exc}. Using temporary directory."
        )

    temp_dir = Path(tempfile.gettempdir()) / "worklog_manager_logs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir, warnings


def _parse_iso_timestamp(value):
    if not value:
        return None
    try:
        return datetime_fromisoformat(value)
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None


def _normalize_shortcut_entry(entry):
    if isinstance(entry, dict):
        normalized = {}
        status = entry.get("status") or entry.get("state")
        if isinstance(status, str):
            normalized["status"] = status
        timestamp = entry.get("timestamp")
        if isinstance(timestamp, str):
            normalized["timestamp"] = timestamp
        version = entry.get("version")
        if isinstance(version, str):
            normalized["version"] = version
        return normalized
    if isinstance(entry, str):
        return {"status": entry}
    return {}


def _shortcut_decision_expired(entry):
    version = entry.get("version")
    if version is None or version != APP_VERSION:
        return True

    timestamp = entry.get("timestamp")
    if not timestamp:
        return True

    recorded = _parse_iso_timestamp(timestamp)
    if recorded is None:
        return True

    if datetime.utcnow() - recorded > _SHORTCUT_DECISION_TTL:
        return True
    return False


def _state_payload(status: str) -> dict:
    # Persist the user's choice along with lightweight context for future resets.
    return {
        "status": status,
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat(),
        "version": APP_VERSION,
    }


class WorklogApplication:
    """
    Main application class that coordinates all components.
    
    This class manages the integration of all Phase 4 components:
    - Settings management
    - Theme system
    - Notification system
    - Backup system
    - System tray integration
    - Keyboard shortcuts
    """
    
    def __init__(self):
        """Initialize the application with all components."""
        self.logger = logging.getLogger(__name__)

        self.single_instance = SingleInstanceManager()
        if not self.single_instance.acquire():
            self.logger.info("Existing Worklog Manager instance detected; activating it instead of starting a new one.")
            notified = self.single_instance.notify_existing()
            if notified:
                self.logger.info("Activation request delivered to running instance.")
            else:
                self.logger.warning("Existing instance did not respond to activation request.")
            raise SystemExit(0)

        self._pending_activation = False
        if self.single_instance:
            self.single_instance.set_activation_callback(self._handle_external_activation)
        
        # Initialize basic managers
        self.settings_manager = SettingsManager()
        
        # Initialize notification manager with default settings
        try:
            settings = self.settings_manager.settings  # Access settings attribute directly
            if hasattr(settings, 'notifications'):
                notification_settings = settings.notifications
            else:
                # Create default notification settings if not available
                from core.settings import NotificationSettings
                notification_settings = NotificationSettings()
            self.notification_manager = NotificationManager(notification_settings)
        except Exception as e:
            self.logger.warning(f"Could not initialize notification manager: {e}")
            self.notification_manager = None
        
        self.backup_manager = BackupManager()
        
        # UI-dependent managers (created later)
        self.theme_manager = None
        self.system_tray_manager = None
        self.keyboard_manager = None
        self.main_window = None
        
        # Setup application
        self._setup_components()
        self._setup_cleanup()
        
    def _setup_components(self):
        """Setup and configure all application components."""
        try:
            # Load settings
            settings = self.settings_manager.settings
            
            # Start notification system
            if self.notification_manager:
                self.notification_manager.start_monitoring()
            
            # Configure backup system
            try:
                if hasattr(settings, 'backup') and settings.backup.auto_backup_enabled:
                    self.backup_manager.setup_automatic_backup(24)  # Daily backup
                else:
                    # Setup default daily backup
                    self.backup_manager.setup_automatic_backup(24)
            except AttributeError:
                # If settings don't have backup config, use defaults
                self.backup_manager.setup_automatic_backup(24)
            
            self.logger.info("All application components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up components: {e}")
            raise
    
    def _setup_cleanup(self):
        """Setup cleanup handlers for graceful shutdown."""
        atexit.register(self.cleanup)

    def _handle_external_activation(self) -> None:
        if self.main_window and getattr(self.main_window, "root", None):
            try:
                self.main_window.root.after(0, self.main_window.show_window)
            except Exception:
                self.logger.exception("Failed to surface main window after activation request")
        else:
            self._pending_activation = True

    def _schedule_desktop_shortcut_prompt(self) -> None:
        if create_shortcut is None or shortcut_exists is None:
            return
        if not getattr(sys, "frozen", False):
            return

        if sys.platform.startswith("win"):
            platform = "windows"
        elif sys.platform.startswith("linux"):
            platform = "linux"
        else:
            return

        existing_shortcut = False
        try:
            existing_shortcut = shortcut_exists(platform, name=APP_SHORTCUT_NAME)
            if existing_shortcut:
                return
        except Exception as exc:
            self.logger.debug("Skipping shortcut prompt: %s", exc)
            return

        state = _load_shortcut_state()
        entry = _normalize_shortcut_entry(state.get(platform))
        state_changed = False

        if entry.get("status") == "created":
            if existing_shortcut:
                return
            state.pop(platform, None)
            state_changed = True
            entry = {}
        elif entry.get("status") == "declined":
            if not _shortcut_decision_expired(entry):
                return
            state.pop(platform, None)
            state_changed = True
            entry = {}

        if state_changed:
            _save_shortcut_state(state)

        def _prompt_user() -> None:
            try:
                from tkinter import messagebox
            except Exception as exc:  # pragma: no cover - Tk unavailable
                self.logger.debug("Shortcut prompt unavailable: %s", exc)
                return

            parent = self.main_window.root if self.main_window else None
            response = messagebox.askyesno(
                "Create Desktop Shortcut?",
                "Would you like to add Worklog Manager to your desktop?",
                parent=parent,
            )

            if not response:
                state[platform] = _state_payload("declined")
                _save_shortcut_state(state)
                return

            try:
                result = create_shortcut(
                    platform,
                    binary=Path(sys.executable),
                    name=APP_SHORTCUT_NAME,
                )
            except Exception as exc:
                self.logger.warning("Desktop shortcut creation failed: %s", exc)
                messagebox.showerror(
                    "Shortcut Creation Failed",
                    f"Could not create the desktop shortcut:\n{exc}",
                    parent=parent,
                )
                return

            state[platform] = _state_payload("created")
            _save_shortcut_state(state)

            summary = f"Shortcut added at {result.desktop}"
            if result.applications and result.applications != result.desktop:
                summary += f"\nLauncher registered at {result.applications}"
            messagebox.showinfo("Shortcut Created", summary, parent=parent)

        if self.main_window and getattr(self.main_window, "root", None):
            self.main_window.root.after(1500, _prompt_user)
    
    def create_main_window(self):
        """Create and configure the main application window."""
        try:
            # Create main window
            self.main_window = MainWindow()

            if self.single_instance:
                self.single_instance.set_activation_callback(self._handle_external_activation)
                if self._pending_activation:
                    self.main_window.root.after(0, self.main_window.show_window)
                    self._pending_activation = False
            
            # Initialize UI-dependent managers after main window exists
            try:
                self.theme_manager = ThemeManager(self.main_window.root)
            except Exception as e:
                self.logger.warning(f"Could not initialize theme manager: {e}")
                self.theme_manager = None
            
            # Setup system tray (after main window exists)
            settings = self.settings_manager.settings
            try:
                if settings.general.system_tray_enabled:
                    self.logger.info("Attempting to initialize system tray...")
                    self.system_tray_manager = SystemTrayManager(self.main_window.root, "Worklog Manager")
                    
                    # Register callbacks for tray menu actions
                    self.system_tray_manager.register_callback("quit_app", self.main_window.quit_application)
                    self.system_tray_manager.register_callback("show_settings", self.main_window.open_settings_from_tray)
                    self.system_tray_manager.register_callback("show_window", self.main_window.show_window)
                    self.system_tray_manager.register_callback("hide_window", self.main_window.hide_window)
                    self.system_tray_manager.register_callback("toggle_window", self.main_window.toggle_window_visibility)
                    
                    # Register work action callbacks (use tray-specific methods without dialogs)
                    self.system_tray_manager.register_callback("start_work", self.main_window.start_work_from_tray)
                    self.system_tray_manager.register_callback("end_work", self.main_window.end_work_from_tray)
                    self.system_tray_manager.register_callback("take_break", self.main_window.take_break_from_tray)
                    self.system_tray_manager.register_callback("end_break", self.main_window.resume_work_from_tray)
                    
                    # Register utility callbacks
                    self.system_tray_manager.register_callback("export_data", self.main_window._export_data)
                    self.system_tray_manager.register_callback("show_summary", self.main_window.show_window)  # Show window to see summary

                    # Configure status monitor hooks for automatic tray updates
                    if getattr(self.system_tray_manager, "status_monitor", None):
                        self.system_tray_manager.status_monitor.set_status_callbacks(
                            self.main_window.get_tray_is_working,
                            self.main_window.get_tray_is_on_break,
                            self.main_window.get_tray_work_start_time,
                        )
                    
                    self.logger.info("Starting system tray...")
                    if self.system_tray_manager.start_tray():
                        self.logger.info("System tray initialized and started successfully")
                        # Pass system tray manager reference to main window
                        self.main_window.system_tray_manager = self.system_tray_manager
                        if getattr(self.system_tray_manager, "status_monitor", None):
                            self.system_tray_manager.status_monitor.start_monitoring()
                        # Sync initial tray status with current worklog state
                        self.main_window._update_system_tray_status()
                    else:
                        self.logger.warning("System tray could not be started")
                        self.system_tray_manager = None
                else:
                    self.logger.info("System tray is disabled in settings")
            except AttributeError as e:
                # Skip system tray if settings don't support it
                self.logger.warning(f"System tray not available: {e}")
                import traceback
                self.logger.warning(traceback.format_exc())
            except Exception as e:
                self.logger.warning(f"Could not initialize system tray: {e}")
                import traceback
                self.logger.warning(traceback.format_exc())
            
            # Setup keyboard shortcuts
            try:
                self.keyboard_manager = KeyboardShortcutManager(self.main_window)
            except Exception as e:
                self.logger.warning(f"Could not setup keyboard shortcuts: {e}")
            
            # Apply theme to main window
            if self.theme_manager:
                try:
                    settings = self.settings_manager.settings
                    if hasattr(settings, 'appearance'):
                        self.theme_manager.apply_theme(settings.appearance.theme)
                    else:
                        self.theme_manager.apply_theme('light')  # Default theme
                except Exception as e:
                    self.logger.warning(f"Could not apply theme: {e}")
            
            self.logger.info("Main window created and configured")
            self._schedule_desktop_shortcut_prompt()
            return self.main_window
            
        except Exception as e:
            self.logger.error(f"Error creating main window: {e}")
            raise
    
    def run(self):
        """Run the application."""
        try:
            # Create main window
            main_window = self.create_main_window()
            
            # Start the application
            self.logger.info(f"Starting Worklog Manager Application v{APP_VERSION}")
            main_window.run()
            
        except Exception as e:
            self.logger.error(f"Error running application: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources on application exit."""
        try:
            self.logger.info("Application cleanup started")
            
            # Stop notification monitoring
            if self.notification_manager:
                self.notification_manager.stop_monitoring()
            
            # Cleanup system tray
            if self.system_tray_manager:
                self.system_tray_manager.cleanup()
            
            # Final backup if needed
            try:
                settings = self.settings_manager.settings
                if hasattr(settings, 'backup') and settings.backup.backup_on_exit:
                    self.backup_manager.create_backup()
                else:
                    # Create backup on exit by default
                    self.backup_manager.create_backup()
            except:
                # Always try to create a final backup
                self.backup_manager.create_backup()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        finally:
            if self.single_instance and self.single_instance.is_primary:
                self.single_instance.release()


def setup_logging():
    """Setup application logging."""
    base_dir = _runtime_base_dir()
    logs_dir, setup_warnings = _prepare_log_directory(base_dir)

    # Create log filename with current date
    log_filename = f"worklog_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = logs_dir / log_filename

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_path), encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Worklog Manager Application Starting")
    logger.info(f"Version: {APP_VERSION}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Runtime Base: {base_dir}")
    logger.info(f"Log Directory: {logs_dir}")
    logger.info(f"Log File: {log_path}")
    logger.info("="*50)

    for warning in setup_warnings:
        logger.warning(warning)


def main():
    """Main application entry point with full Phase 4 integration."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)

        logger.info(f"Initializing Worklog Manager v{APP_VERSION} with advanced features...")

        # Create and run the comprehensive application
        app = WorklogApplication()
        app.run()

        logger.info("Application shutdown normally")

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        logging.getLogger(__name__).info("Application interrupted by user")
        
    except Exception as e:
        error_msg = f"Fatal error: {e}"
        print(error_msg)
        logging.getLogger(__name__).critical(error_msg, exc_info=True)
        
        # Show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            messagebox.showerror("Fatal Error", 
                               f"The Worklog Manager encountered a fatal error:\n\n{e}\n\n"
                               f"Please check the log file for more details.\n"
                               f"Log location: logs/worklog_{datetime.now().strftime('%Y%m%d')}.log")
            root.destroy()
        except:
            pass  # If GUI is not available, just exit
        
        sys.exit(1)


if __name__ == "__main__":
    main()