"""Settings and configuration models for the Worklog Manager."""

import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import time, timedelta


class Theme(Enum):
    """Available application themes."""
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"
    AUTO = "auto"  # Follow system theme


class NotificationType(Enum):
    """Types of notifications."""
    WORK_REMINDER = "work_reminder"
    BREAK_REMINDER = "break_reminder" 
    OVERTIME_WARNING = "overtime_warning"
    DAY_END_REMINDER = "day_end_reminder"
    BACKUP_COMPLETE = "backup_complete"


class TimeFormat(Enum):
    """Time display formats."""
    HOURS_12 = "12h"  # 2:30 PM
    HOURS_24 = "24h"  # 14:30


class DateFormat(Enum):
    """Date display formats."""
    MDY = "mdy"  # MM/DD/YYYY
    DMY = "dmy"  # DD/MM/YYYY
    YMD = "ymd"  # YYYY-MM-DD


@dataclass
class WorkNormSettings:
    """Work norm and time-related settings."""
    daily_work_hours: float = 7.5  # Standard work day in hours
    daily_work_minutes: int = 450   # Daily work in minutes (7.5 * 60)
    
    # Break settings
    max_break_duration: int = 120   # Maximum single break in minutes
    max_daily_break_time: int = 90  # Maximum total break time per day
    lunch_break_duration: int = 30  # Default lunch break duration
    coffee_break_duration: int = 15 # Default coffee break duration
    
    # Overtime settings
    overtime_threshold: float = 8.0 # Hours before overtime kicks in
    max_overtime_hours: float = 3.0 # Maximum overtime per day
    
    # Work time validation
    min_work_session: int = 5       # Minimum work session in minutes
    max_work_day_hours: float = 16.0 # Maximum work day length
    
    def __post_init__(self):
        """Validate settings after initialization."""
        self.daily_work_minutes = int(self.daily_work_hours * 60)


@dataclass  
class NotificationSettings:
    """Notification and reminder settings."""
    enabled: bool = True
    
    # Work reminders
    work_start_reminder: bool = True
    work_start_time: str = "09:00"  # Time format HH:MM
    
    # Break reminders
    break_reminders: bool = True
    break_reminder_interval: int = 120  # Minutes between break reminders
    long_work_warning: int = 180       # Warn after X minutes of continuous work
    
    # End of day
    end_day_reminder: bool = True
    end_day_time: str = "17:30"       # Suggest ending work at this time
    
    # Overtime warnings
    overtime_warnings: bool = True
    overtime_warning_threshold: float = 0.5  # Warn X hours before overtime
    
    # System notifications
    system_notifications: bool = True
    sound_notifications: bool = True
    
    # Backup notifications
    backup_notifications: bool = True


@dataclass
class AppearanceSettings:
    """Appearance and UI settings."""
    theme: Theme = Theme.LIGHT
    
    # Window settings
    window_width: int = 600
    window_height: int = 500
    window_maximized: bool = False
    remember_window_position: bool = True
    window_x: int = 100
    window_y: int = 100
    
    # Font settings
    font_family: str = "Arial"
    font_size: int = 10
    
    # Display formats
    time_format: TimeFormat = TimeFormat.HOURS_24
    date_format: DateFormat = DateFormat.YMD
    
    # UI behavior
    minimize_to_tray: bool = True
    start_minimized: bool = False
    close_to_tray: bool = True
    show_seconds: bool = True
    
    # Colors (hex codes)
    accent_color: str = "#0078d4"
    working_color: str = "#28a745"
    break_color: str = "#ffc107"
    overtime_color: str = "#dc3545"


@dataclass
class BackupSettings:
    """Backup and data management settings."""
    auto_backup: bool = True
    backup_frequency: int = 24        # Hours between backups
    backup_retention_days: int = 30   # Keep backups for X days
    backup_location: str = "backups"  # Backup directory
    compress_backups: bool = True     # Compress backup files
    backup_on_exit: bool = True       # Create backup when exiting application
    
    # Export settings
    auto_export: bool = False
    export_frequency: int = 7         # Days between auto-exports
    export_format: str = "csv"        # Default export format
    export_location: str = "exports"  # Export directory
    
    # Data retention
    data_retention_months: int = 12   # Keep data for X months
    compress_old_data: bool = True    # Compress data older than 6 months


@dataclass
class KeyboardShortcuts:
    """Keyboard shortcut settings."""
    start_work: str = "Ctrl+S"        # Start work/day
    end_work: str = "Ctrl+E"          # End work/day
    take_break: str = "Ctrl+B"        # Take break
    end_break: str = "Ctrl+R"         # End break/resume work
    show_summary: str = "Ctrl+M"      # Show summary
    export_data: str = "Ctrl+Shift+E" # Export data
    settings: str = "Ctrl+,"          # Open settings
    quit_app: str = "Ctrl+Q"          # Quit application
    
    # Additional shortcuts for legacy compatibility
    start_day: str = "Ctrl+S"         # Legacy alias for start_work
    stop_work: str = "Ctrl+P"         # P for Pause
    continue_work: str = "Ctrl+R"     # R for Resume  
    end_day: str = "Ctrl+E"           # Legacy alias for end_work
    revoke_action: str = "Ctrl+Z"     # Revoke last action
    reset_day: str = "Ctrl+Shift+R"   # Reset day
    help: str = "F1"                  # Help
    quit: str = "Ctrl+Q"              # Legacy alias for quit_app
    
    # Global hotkeys (work when app is minimized)
    global_start_day: str = "Ctrl+Alt+S"
    global_stop_work: str = "Ctrl+Alt+P"
    global_continue_work: str = "Ctrl+Alt+R"


@dataclass
class GeneralSettings:
    """General application settings."""
    # Startup behavior
    start_with_system: bool = False
    start_minimized: bool = False
    auto_start_work_on_open: bool = False
    check_for_updates: bool = True
    
    # System tray
    system_tray_enabled: bool = True
    minimize_to_tray: bool = True
    
    # Exit behavior
    confirm_exit: bool = True
    save_on_exit: bool = True
    
    # Data behavior  
    auto_save: bool = True
    save_interval: int = 60           # Seconds between auto-saves
    
    # Language and locale
    language: str = "en_US"
    date_format: str = "%Y-%m-%d"     # Date format for display
    timezone: str = "auto"            # Auto-detect or specific timezone
    
    # Debug and logging
    debug_mode: bool = False
    log_level: str = "INFO"           # DEBUG, INFO, WARNING, ERROR
    keep_log_days: int = 7            # Days to keep log files
    
    # Performance
    database_cache_size: int = 1000   # Number of records to cache
    ui_update_interval: int = 1       # Seconds between UI updates


@dataclass
class UserSettings:
    """Complete user settings configuration."""
    work_norms: WorkNormSettings = None
    notifications: NotificationSettings = None
    appearance: AppearanceSettings = None
    backup: BackupSettings = None
    shortcuts: KeyboardShortcuts = None
    general: GeneralSettings = None
    
    # Metadata
    version: str = "1.0"
    created_at: str = ""
    modified_at: str = ""
    
    def __post_init__(self):
        """Initialize default settings if not provided."""
        if self.work_norms is None:
            self.work_norms = WorkNormSettings()
        if self.notifications is None:
            self.notifications = NotificationSettings()
        if self.appearance is None:
            self.appearance = AppearanceSettings()
        if self.backup is None:
            self.backup = BackupSettings()
        if self.shortcuts is None:
            self.shortcuts = KeyboardShortcuts()
        if self.general is None:
            self.general = GeneralSettings()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """Create UserSettings from dictionary."""
        # Handle nested dataclasses
        if 'work_norms' in data and isinstance(data['work_norms'], dict):
            data['work_norms'] = WorkNormSettings(**data['work_norms'])
        if 'notifications' in data and isinstance(data['notifications'], dict):
            data['notifications'] = NotificationSettings(**data['notifications'])
        if 'appearance' in data and isinstance(data['appearance'], dict):
            # Handle enum conversion
            appearance_data = data['appearance'].copy()
            if 'theme' in appearance_data and isinstance(appearance_data['theme'], str):
                appearance_data['theme'] = Theme(appearance_data['theme'])
            if 'time_format' in appearance_data and isinstance(appearance_data['time_format'], str):
                appearance_data['time_format'] = TimeFormat(appearance_data['time_format'])
            if 'date_format' in appearance_data and isinstance(appearance_data['date_format'], str):
                appearance_data['date_format'] = DateFormat(appearance_data['date_format'])
            data['appearance'] = AppearanceSettings(**appearance_data)
        if 'backup' in data and isinstance(data['backup'], dict):
            data['backup'] = BackupSettings(**data['backup'])
        if 'shortcuts' in data and isinstance(data['shortcuts'], dict):
            data['shortcuts'] = KeyboardShortcuts(**data['shortcuts'])
        if 'general' in data and isinstance(data['general'], dict):
            data['general'] = GeneralSettings(**data['general'])
        
        return cls(**data)


class SettingsManager:
    """Manages loading, saving, and validation of user settings."""
    
    def __init__(self, settings_file: str = "settings.json"):
        """Initialize settings manager.
        
        Args:
            settings_file: Path to settings file
        """
        self.settings_file = settings_file
        self.settings: UserSettings = UserSettings()
        self.logger = logging.getLogger(__name__)
        
        # Load existing settings or create defaults
        self.load_settings()
    
    def load_settings(self) -> bool:
        """Load settings from file.
        
        Returns:
            True if loaded successfully, False if using defaults
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.settings = UserSettings.from_dict(data)
                self.logger.info(f"Settings loaded from {self.settings_file}")
                return True
            else:
                self.logger.info("No settings file found, using defaults")
                self.save_settings()  # Create default settings file
                return False
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            self.settings = UserSettings()  # Reset to defaults
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from datetime import datetime
            
            # Update modification time
            self.settings.modified_at = datetime.now().isoformat()
            if not self.settings.created_at:
                self.settings.created_at = self.settings.modified_at
            
            # Convert to dict and save
            settings_dict = self.settings.to_dict()
            
            # Custom JSON encoder for enums
            def json_encoder(obj):
                if hasattr(obj, 'value'):
                    return obj.value
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(settings_dict, file, indent=2, default=json_encoder)
            
            self.logger.info(f"Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, category: str, setting: str, default=None):
        """Get a specific setting value.
        
        Args:
            category: Settings category (work_norms, notifications, etc.)
            setting: Setting name
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        try:
            category_obj = getattr(self.settings, category, None)
            if category_obj:
                return getattr(category_obj, setting, default)
            return default
        except Exception:
            return default
    
    def set_setting(self, category: str, setting: str, value) -> bool:
        """Set a specific setting value.
        
        Args:
            category: Settings category
            setting: Setting name  
            value: New value
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            category_obj = getattr(self.settings, category, None)
            if category_obj and hasattr(category_obj, setting):
                setattr(category_obj, setting, value)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set setting {category}.{setting}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults.
        
        Returns:
            True if reset successfully, False otherwise
        """
        try:
            self.settings = UserSettings()
            return self.save_settings()
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            return False
    
    def export_settings(self, filepath: str) -> bool:
        """Export settings to a file.
        
        Args:
            filepath: Export file path
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            settings_dict = self.settings.to_dict()
            
            def json_encoder(obj):
                if hasattr(obj, 'value'):
                    return obj.value
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(settings_dict, file, indent=2, default=json_encoder)
            
            self.logger.info(f"Settings exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """Import settings from a file.
        
        Args:
            filepath: Import file path
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.settings = UserSettings.from_dict(data)
            
            # Save imported settings
            success = self.save_settings()
            if success:
                self.logger.info(f"Settings imported from {filepath}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False
    
    def validate_settings(self) -> List[str]:
        """Validate current settings and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        try:
            # Validate work norms
            wn = self.settings.work_norms
            if wn.daily_work_hours <= 0 or wn.daily_work_hours > 24:
                issues.append("Daily work hours must be between 0 and 24")
            
            if wn.max_break_duration <= 0:
                issues.append("Maximum break duration must be positive")
            
            if wn.overtime_threshold <= wn.daily_work_hours:
                issues.append("Overtime threshold should be higher than daily work hours")
            
            # Validate appearance settings
            app = self.settings.appearance
            if app.window_width < 400 or app.window_height < 300:
                issues.append("Window size too small (minimum 400x300)")
            
            # Validate backup settings
            backup = self.settings.backup
            if backup.backup_retention_days < 1:
                issues.append("Backup retention must be at least 1 day")
            
            if backup.data_retention_months < 1:
                issues.append("Data retention must be at least 1 month")
            
        except Exception as e:
            issues.append(f"Settings validation error: {e}")
        
        return issues