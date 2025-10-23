"""
Settings Dialog for Worklog Manager Application

Comprehensive settings interface with tabbed organization for all configuration options.
Provides user-friendly controls for customizing application behavior and appearance.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import os
from datetime import datetime
from typing import Dict, Optional, Callable

from core.settings import SettingsManager, UserSettings
from gui.theme_manager import ThemeManager, ThemePreview
from core.simple_backup_manager import BackupManager

# Compatibility wrapper for ttk.Spinbox on Python versions that lack it.
if not hasattr(ttk, 'Spinbox'):
    class TtkSpinboxCompat(tk.Spinbox):
        """Compatibility wrapper for ttk.Spinbox using tk.Spinbox."""

        def __init__(self, parent, **kwargs):
            tk_kwargs = kwargs.copy()
            if 'from' in tk_kwargs and 'from_' not in tk_kwargs:
                tk_kwargs['from_'] = tk_kwargs.pop('from')
            tk_kwargs.setdefault('width', 10)
            tk_kwargs.setdefault('justify', 'center')
            super().__init__(parent, **tk_kwargs)

    ttk.Spinbox = TtkSpinboxCompat

class SettingsDialog:
    """Main settings dialog with tabbed interface for all configuration options."""
    
    def __init__(self, parent: tk.Widget, settings_manager: SettingsManager,
                 theme_manager: ThemeManager = None, backup_manager: BackupManager = None,
                 on_settings_changed: Callable = None):
        self.parent = parent
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.backup_manager = backup_manager
        self.on_settings_changed = on_settings_changed
        self.initial_theme = theme_manager.current_theme if theme_manager else None
        self.theme_applied = False
        self._saving = False  # Flag to prevent concurrent saves
        
        # Load current settings (force reload to get latest values)
        self.settings_manager.load_settings()  # Ensure settings are loaded
        self.settings = self.settings_manager.settings
        self.original_settings = self.settings_manager.settings  # For cancel functionality
        
        self.dialog = None
        self.notebook = None
        self.tabs = {}
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the main settings dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Worklog Manager Settings")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.minsize(600, 400)  # Set minimum size
        
        # Apply theme background to dialog
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            self.dialog.configure(bg=colors['bg_primary'])
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_settings)
        
        # Center the dialog
        self.center_dialog()
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, style="Themed.TFrame")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create content frame (for notebook) that can expand
        content_frame = ttk.Frame(main_frame, style="Themed.TFrame")
        content_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create notebook for tabs in the content frame
        self.notebook = ttk.Notebook(content_frame, style="Themed.TNotebook")
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.create_work_norms_tab()
        self.create_appearance_tab()
        self.create_notifications_tab()
        self.create_backup_tab()
        self.create_keyboard_shortcuts_tab()
        self.create_general_tab()
        
        # Update UI with current settings to ensure all values are properly loaded
        self.update_ui_with_settings(self.settings)
        
        # Create fixed button frame at bottom (doesn't expand)
        self.create_button_frame(main_frame)
    
    def create_button_frame(self, parent):
        """Create the button frame that stays fixed at the bottom."""
        
        # Create button frame
        button_frame = ttk.Frame(parent, style="Themed.TFrame")
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Left side buttons (utility functions)
        left_frame = ttk.Frame(button_frame, style="Themed.TFrame")
        left_frame.pack(side='left')
        
        ttk.Button(left_frame, text="Reset to Defaults", command=self.reset_to_defaults, style="Themed.TButton").pack(side='left')
        ttk.Button(left_frame, text="Import Settings", command=self.import_settings, style="Themed.TButton").pack(side='left', padx=(5, 0))
        ttk.Button(left_frame, text="Export Settings", command=self.export_settings, style="Themed.TButton").pack(side='left', padx=(5, 0))
        
        # Right side buttons (main actions)
        right_frame = ttk.Frame(button_frame, style="Themed.TFrame")
        right_frame.pack(side='right')
        
        ttk.Button(right_frame, text="Cancel", command=self.cancel_settings, style="Themed.TButton").pack(side='right', padx=(5, 0))
        ttk.Button(right_frame, text="Apply", command=self.apply_settings, style="Themed.TButton").pack(side='right', padx=(5, 0))
        ttk.Button(right_frame, text="OK", command=self.ok_settings, style="Themed.TButton").pack(side='right', padx=(5, 0))
    
    def create_scrollable_frame(self, parent):
        """Create a scrollable frame with mouse wheel support."""
        # Get current theme colors
        colors = self.theme_manager.get_theme_colors() if self.theme_manager else {'bg_primary': '#ffffff'}
        
        # Create canvas and scrollbar with themed background
        canvas = tk.Canvas(parent, highlightthickness=0, bg=colors['bg_primary'])
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel support
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mouse wheel to canvas and all child widgets
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Pack elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame, canvas
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_work_norms_tab(self):
        """Create the work norms settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Work Norms")
        self.tabs['work_norms'] = {}
        
        # Create scrollable frame
        scrollable_frame, canvas = self.create_scrollable_frame(frame)
        
        # Daily work settings
        work_group = ttk.LabelFrame(scrollable_frame, text="Daily Work Settings", padding=10)
        work_group.pack(fill='x', padx=10, pady=5)
        
        # Hours per day
        ttk.Label(work_group, text="Hours per day:").grid(row=0, column=0, sticky='w', pady=2)
        hours_var = tk.DoubleVar(value=self.settings.work_norms.daily_work_hours)
        hours_spinbox = ttk.Spinbox(work_group, from_=1.0, to=24.0, increment=0.5, 
                                   textvariable=hours_var, width=10)
        hours_spinbox.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['daily_work_hours'] = hours_var
        
        # Minutes per day (calculated field)\n        ttk.Label(work_group, text="Minutes per day:").grid(row=1, column=0, sticky='w', pady=2)
        minutes_label = ttk.Label(work_group, text=str(int(self.settings.work_norms.daily_work_hours * 60)))
        minutes_label.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['minutes_label'] = minutes_label
        
        # Update minutes when hours change
        def update_minutes(*args):
            try:
                minutes = int(hours_var.get() * 60)
                minutes_label.config(text=str(minutes))
            except:
                pass
        hours_var.trace('w', update_minutes)
        
        # Break settings
        break_group = ttk.LabelFrame(scrollable_frame, text="Break Settings", padding=10)
        break_group.pack(fill='x', padx=10, pady=5)
        
        # Max break duration
        ttk.Label(break_group, text="Max break duration (minutes):").grid(row=0, column=0, sticky='w', pady=2)
        max_break_var = tk.IntVar(value=self.settings.work_norms.max_break_duration)
        ttk.Spinbox(break_group, from_=1, to=240, increment=5, 
                   textvariable=max_break_var, width=10).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['max_break_duration'] = max_break_var
        
        # Total break limit
        ttk.Label(break_group, text="Daily break limit (minutes):").grid(row=1, column=0, sticky='w', pady=2)
        break_limit_var = tk.IntVar(value=self.settings.work_norms.max_daily_break_time)
        ttk.Spinbox(break_group, from_=0, to=480, increment=15, 
                   textvariable=break_limit_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['daily_break_limit'] = break_limit_var
        
        # Overtime settings
        overtime_group = ttk.LabelFrame(scrollable_frame, text="Overtime Settings", padding=10)
        overtime_group.pack(fill='x', padx=10, pady=5)
        
        # Overtime threshold
        ttk.Label(overtime_group, text="Overtime threshold (hours):").grid(row=0, column=0, sticky='w', pady=2)
        overtime_var = tk.DoubleVar(value=self.settings.work_norms.overtime_threshold)
        ttk.Spinbox(overtime_group, from_=1.0, to=24.0, increment=0.5, 
                   textvariable=overtime_var, width=10).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['overtime_threshold'] = overtime_var
        
        # Warning threshold
        ttk.Label(overtime_group, text="Warning threshold (hours):").grid(row=1, column=0, sticky='w', pady=2)
        warning_var = tk.DoubleVar(value=self.settings.work_norms.overtime_threshold - 0.5)  # Default to 30 min before overtime
        ttk.Spinbox(overtime_group, from_=1.0, to=24.0, increment=0.5, 
                   textvariable=warning_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['work_norms']['warning_threshold'] = warning_var
    
    def create_appearance_tab(self):
        """Create the appearance settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Appearance")
        self.tabs['appearance'] = {}
        
        # Create scrollable frame
        scrollable_frame, canvas = self.create_scrollable_frame(frame)
        
        # Theme selection
        theme_group = ttk.LabelFrame(scrollable_frame, text="Theme", padding=10)
        theme_group.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(theme_group, text="Current theme:").grid(row=0, column=0, sticky='w', pady=2)
        
        # Handle theme value - convert enum to string if necessary
        theme_value = self.settings.appearance.theme
        if hasattr(theme_value, 'value'):
            theme_value = theme_value.value
        theme_var = tk.StringVar(value=theme_value)
        theme_combo = ttk.Combobox(theme_group, textvariable=theme_var, state='readonly')
        
        if self.theme_manager:
            available_themes = self.theme_manager.get_available_themes()
            theme_combo['values'] = available_themes
        
        theme_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['appearance']['theme'] = theme_var
        
        # Theme preview
        if self.theme_manager:
            preview_frame = ttk.LabelFrame(scrollable_frame, text="Theme Preview", padding=10)
            preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            preview = ThemePreview(preview_frame, self.theme_manager)
            preview.update_preview(theme_var.get())
            
            def on_theme_change(*args):
                preview.update_preview(theme_var.get())
            
            theme_var.trace('w', on_theme_change)
        
        # Font settings
        font_group = ttk.LabelFrame(scrollable_frame, text="Font Settings", padding=10)
        font_group.pack(fill='x', padx=10, pady=5)
        
        # Font family
        ttk.Label(font_group, text="Font family:").grid(row=0, column=0, sticky='w', pady=2)
        font_var = tk.StringVar(value=self.settings.appearance.font_family)
        font_combo = ttk.Combobox(font_group, textvariable=font_var)
        font_combo['values'] = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana', 'Tahoma']
        font_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['appearance']['font_family'] = font_var
        
        # Font size
        ttk.Label(font_group, text="Font size:").grid(row=1, column=0, sticky='w', pady=2)
        font_size_var = tk.IntVar(value=self.settings.appearance.font_size)
        ttk.Spinbox(font_group, from_=8, to=24, increment=1, 
                   textvariable=font_size_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['appearance']['font_size'] = font_size_var
        
        # Window settings
        window_group = ttk.LabelFrame(scrollable_frame, text="Window Settings", padding=10)
        window_group.pack(fill='x', padx=10, pady=5)
        
        # Window dimensions
        ttk.Label(window_group, text="Window width:").grid(row=0, column=0, sticky='w', pady=2)
        window_width_var = tk.IntVar(value=self.settings.appearance.window_width)
        ttk.Spinbox(window_group, from_=400, to=2000, increment=50, 
                   textvariable=window_width_var, width=10).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['appearance']['window_width'] = window_width_var
        
        ttk.Label(window_group, text="Window height:").grid(row=1, column=0, sticky='w', pady=2)
        window_height_var = tk.IntVar(value=self.settings.appearance.window_height)
        ttk.Spinbox(window_group, from_=300, to=1500, increment=50, 
                   textvariable=window_height_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['appearance']['window_height'] = window_height_var
        
        # Start maximized
        window_maximized_var = tk.BooleanVar(value=self.settings.appearance.window_maximized)
        ttk.Checkbutton(window_group, text="Start window maximized", 
                       variable=window_maximized_var).grid(row=2, column=0, columnspan=2, sticky='w', pady=2)
        self.tabs['appearance']['window_maximized'] = window_maximized_var
        
        # Remember window position
        remember_pos_var = tk.BooleanVar(value=self.settings.appearance.remember_window_position)
        ttk.Checkbutton(window_group, text="Remember window position", 
                       variable=remember_pos_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        self.tabs['appearance']['remember_position'] = remember_pos_var
        
        # Remember window size
        remember_size_var = tk.BooleanVar(value=self.settings.appearance.remember_window_position)
        ttk.Checkbutton(window_group, text="Remember window size", 
                       variable=remember_size_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        self.tabs['appearance']['remember_size'] = remember_size_var
    
    def create_notifications_tab(self):
        """Create the notifications settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Notifications")
        self.tabs['notifications'] = {}
        
        # Create scrollable frame
        scrollable_frame, canvas = self.create_scrollable_frame(frame)
        
        # General notification settings
        general_group = ttk.LabelFrame(scrollable_frame, text="General Settings", padding=10)
        general_group.pack(fill='x', padx=10, pady=5)
        
        # Enable notifications
        enable_var = tk.BooleanVar(value=self.settings.notifications.enabled)
        ttk.Checkbutton(general_group, text="Enable notifications", 
                       variable=enable_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['notifications']['enabled'] = enable_var
        
        # System notifications
        system_var = tk.BooleanVar(value=self.settings.notifications.system_notifications)
        ttk.Checkbutton(general_group, text="Use system notifications", 
                       variable=system_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['notifications']['system_notifications'] = system_var
        
        # Work reminders
        work_group = ttk.LabelFrame(scrollable_frame, text="Work Reminders", padding=10)
        work_group.pack(fill='x', padx=10, pady=5)
        
        # Start work reminder
        start_reminder_var = tk.BooleanVar(value=self.settings.notifications.work_start_reminder)
        ttk.Checkbutton(work_group, text="Remind to start work", 
                       variable=start_reminder_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['notifications']['work_start_reminder'] = start_reminder_var
        
        # Start work time
        ttk.Label(work_group, text="Start work time:").grid(row=1, column=0, sticky='w', pady=2)
        start_time_var = tk.StringVar(value=self.settings.notifications.work_start_time)
        start_time_entry = ttk.Entry(work_group, textvariable=start_time_var, width=10)
        start_time_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['notifications']['work_start_time'] = start_time_var
        
        # Break reminders
        break_group = ttk.LabelFrame(scrollable_frame, text="Break Reminders", padding=10)
        break_group.pack(fill='x', padx=10, pady=5)
        
        # Break reminder
        break_reminder_var = tk.BooleanVar(value=self.settings.notifications.break_reminders)
        ttk.Checkbutton(break_group, text="Remind to take breaks", 
                       variable=break_reminder_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['notifications']['break_reminder'] = break_reminder_var
        
        # Break interval
        ttk.Label(break_group, text="Break interval (minutes):").grid(row=1, column=0, sticky='w', pady=2)
        break_interval_var = tk.IntVar(value=self.settings.notifications.break_reminder_interval)
        ttk.Spinbox(break_group, from_=15, to=240, increment=15, 
                   textvariable=break_interval_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['notifications']['break_reminder_interval'] = break_interval_var
        
        # Overtime warnings
        overtime_group = ttk.LabelFrame(scrollable_frame, text="Overtime Warnings", padding=10)
        overtime_group.pack(fill='x', padx=10, pady=5)
        
        # Overtime warning
        overtime_warning_var = tk.BooleanVar(value=self.settings.notifications.overtime_warnings)
        ttk.Checkbutton(overtime_group, text="Warn about overtime", 
                       variable=overtime_warning_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['notifications']['overtime_warning'] = overtime_warning_var
        
        # End day reminder
        end_day_var = tk.BooleanVar(value=self.settings.notifications.end_day_reminder)
        ttk.Checkbutton(overtime_group, text="Remind to end work day", 
                       variable=end_day_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['notifications']['end_day_reminder'] = end_day_var
        
        # End day time
        ttk.Label(overtime_group, text="End day time:").grid(row=2, column=0, sticky='w', pady=2)
        end_time_var = tk.StringVar(value=self.settings.notifications.end_day_time)
        end_time_entry = ttk.Entry(overtime_group, textvariable=end_time_var, width=10)
        end_time_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['notifications']['end_day_time'] = end_time_var
    
    def create_backup_tab(self):
        """Create the backup settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Backup")
        self.tabs['backup'] = {}
        
        # Auto backup settings
        auto_group = ttk.LabelFrame(frame, text="Automatic Backup", padding=10)
        auto_group.pack(fill='x', padx=10, pady=5)
        
        # Enable auto backup
        auto_enabled_var = tk.BooleanVar(value=self.settings.backup.auto_backup)
        ttk.Checkbutton(auto_group, text="Enable automatic backup", 
                       variable=auto_enabled_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['backup']['auto_backup_enabled'] = auto_enabled_var
        
        # Backup frequency
        ttk.Label(auto_group, text="Backup frequency:").grid(row=1, column=0, sticky='w', pady=2)
        frequency_var = tk.StringVar(value=self.settings.backup.backup_frequency)
        frequency_combo = ttk.Combobox(auto_group, textvariable=frequency_var, state='readonly')
        frequency_combo['values'] = ['daily', 'weekly', 'monthly']
        frequency_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['backup']['backup_frequency'] = frequency_var
        
        # Backup time
        ttk.Label(auto_group, text="Backup time:").grid(row=2, column=0, sticky='w', pady=2)
        backup_time_var = tk.StringVar(value="23:00")  # Default backup time
        ttk.Entry(auto_group, textvariable=backup_time_var, width=10).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['backup']['backup_time'] = backup_time_var
        
        # Backup directory
        ttk.Label(auto_group, text="Backup directory:").grid(row=3, column=0, sticky='w', pady=2)
        backup_dir_var = tk.StringVar(value=self.settings.backup.backup_location)
        dir_frame = ttk.Frame(auto_group)
        dir_frame.grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Entry(dir_frame, textvariable=backup_dir_var).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", 
                  command=lambda: self.browse_directory(backup_dir_var)).pack(side='right', padx=(5, 0))
        self.tabs['backup']['backup_directory'] = backup_dir_var
        
        auto_group.columnconfigure(1, weight=1)
        
        # Retention settings
        retention_group = ttk.LabelFrame(frame, text="Retention Settings", padding=10)
        retention_group.pack(fill='x', padx=10, pady=5)
        
        # Max backup files
        ttk.Label(retention_group, text="Max backup files:").grid(row=0, column=0, sticky='w', pady=2)
        max_files_var = tk.IntVar(value=10)  # Default max backup files
        ttk.Spinbox(retention_group, from_=1, to=100, increment=1, 
                   textvariable=max_files_var, width=10).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['backup']['max_backup_files'] = max_files_var
        
        # Retention days
        ttk.Label(retention_group, text="Retention days:").grid(row=1, column=0, sticky='w', pady=2)
        retention_days_var = tk.IntVar(value=self.settings.backup.backup_retention_days)
        ttk.Spinbox(retention_group, from_=1, to=365, increment=1, 
                   textvariable=retention_days_var, width=10).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['backup']['retention_days'] = retention_days_var
        
        # Options
        options_group = ttk.LabelFrame(frame, text="Backup Options", padding=10)
        options_group.pack(fill='x', padx=10, pady=5)
        
        # Compress backups
        compress_var = tk.BooleanVar(value=self.settings.backup.compress_backups)
        ttk.Checkbutton(options_group, text="Compress backups", 
                       variable=compress_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['backup']['compress_backups'] = compress_var
        
        # Backup on exit
        exit_backup_var = tk.BooleanVar(value=self.settings.backup.backup_on_exit)
        ttk.Checkbutton(options_group, text="Backup on exit", 
                       variable=exit_backup_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['backup']['backup_on_exit'] = exit_backup_var
        
        # Manual backup button
        manual_group = ttk.LabelFrame(frame, text="Manual Backup", padding=10)
        manual_group.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(manual_group, text="Create Backup Now", 
                  command=self.create_manual_backup).pack(side='left')
        ttk.Button(manual_group, text="View Backup List", 
                  command=self.show_backup_list).pack(side='left', padx=(10, 0))
    
    def create_keyboard_shortcuts_tab(self):
        """Create the keyboard shortcuts settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Shortcuts")
        self.tabs['shortcuts'] = {}
        
        # Create scrollable frame
        scrollable_frame, canvas = self.create_scrollable_frame(frame)
        
        # Instructions
        info_frame = ttk.Frame(scrollable_frame)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(info_frame, text="Configure keyboard shortcuts for common actions:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text="Use format: Ctrl+Key, Alt+Key, Shift+Key, or combinations like Ctrl+Shift+Key").pack(anchor='w')
        
        # Shortcuts
        shortcuts_group = ttk.LabelFrame(scrollable_frame, text="Keyboard Shortcuts", padding=10)
        shortcuts_group.pack(fill='x', padx=10, pady=5)
        
        shortcuts = [
            ('start_work', 'Start Work', self.settings.shortcuts.start_work),
            ('end_work', 'End Work', self.settings.shortcuts.end_work),
            ('take_break', 'Take Break', self.settings.shortcuts.take_break),
            ('end_break', 'End Break', self.settings.shortcuts.end_break),
            ('show_summary', 'Show Summary', self.settings.shortcuts.show_summary),
            ('export_data', 'Export Data', self.settings.shortcuts.export_data),
            ('settings', 'Open Settings', self.settings.shortcuts.settings),
            ('quit_app', 'Quit Application', self.settings.shortcuts.quit_app)
        ]
        
        for i, (key, label, default_value) in enumerate(shortcuts):
            ttk.Label(shortcuts_group, text=f"{label}:").grid(row=i, column=0, sticky='w', pady=2)
            
            shortcut_var = tk.StringVar(value=default_value)
            entry = ttk.Entry(shortcuts_group, textvariable=shortcut_var, width=20)
            entry.grid(row=i, column=1, sticky='w', padx=(10, 5), pady=2)
            
            # Capture button
            capture_btn = ttk.Button(shortcuts_group, text="Capture", 
                                   command=lambda v=shortcut_var: self.capture_shortcut(v))
            capture_btn.grid(row=i, column=2, padx=5, pady=2)
            
            # Clear button
            clear_btn = ttk.Button(shortcuts_group, text="Clear", 
                                 command=lambda v=shortcut_var: v.set(""))
            clear_btn.grid(row=i, column=3, padx=5, pady=2)
            
            self.tabs['shortcuts'][key] = shortcut_var
        
    def create_general_tab(self):
        """Create the general settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="General")
        self.tabs['general'] = {}
        
        # Startup settings
        startup_group = ttk.LabelFrame(frame, text="Startup Options", padding=10)
        startup_group.pack(fill='x', padx=10, pady=5)
        
        # Start minimized
        minimized_var = tk.BooleanVar(value=self.settings.general.start_minimized)
        ttk.Checkbutton(startup_group, text="Start minimized to system tray", 
                       variable=minimized_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['general']['start_minimized'] = minimized_var
        
        # Auto start work
        auto_start_var = tk.BooleanVar(value=self.settings.general.auto_start_work_on_open)
        ttk.Checkbutton(startup_group, text="Auto-start work session on open", 
                       variable=auto_start_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['general']['auto_start_work'] = auto_start_var
        
        # System integration
        system_group = ttk.LabelFrame(frame, text="System Integration", padding=10)
        system_group.pack(fill='x', padx=10, pady=5)
        
        # System tray
        tray_var = tk.BooleanVar(value=self.settings.general.system_tray_enabled)
        ttk.Checkbutton(system_group, text="Enable system tray icon", 
                       variable=tray_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['general']['system_tray_enabled'] = tray_var
        
        # Minimize to tray
        minimize_tray_var = tk.BooleanVar(value=self.settings.general.minimize_to_tray)
        ttk.Checkbutton(system_group, text="Minimize to system tray", 
                       variable=minimize_tray_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['general']['minimize_to_tray'] = minimize_tray_var
        
        # Data settings
        data_group = ttk.LabelFrame(frame, text="Data Management", padding=10)
        data_group.pack(fill='x', padx=10, pady=5)
        
        # Confirm exit
        confirm_exit_var = tk.BooleanVar(value=self.settings.general.confirm_exit)
        ttk.Checkbutton(data_group, text="Confirm before exit", 
                       variable=confirm_exit_var).grid(row=0, column=0, sticky='w', pady=2)
        self.tabs['general']['confirm_exit'] = confirm_exit_var
        
        # Save on exit
        save_exit_var = tk.BooleanVar(value=self.settings.general.save_on_exit)
        ttk.Checkbutton(data_group, text="Auto-save data on exit", 
                       variable=save_exit_var).grid(row=1, column=0, sticky='w', pady=2)
        self.tabs['general']['save_on_exit'] = save_exit_var
        
        # Language settings (placeholder for future)
        lang_group = ttk.LabelFrame(frame, text="Language & Region", padding=10)
        lang_group.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(lang_group, text="Language:").grid(row=0, column=0, sticky='w', pady=2)
        language_var = tk.StringVar(value=self.settings.general.language)
        language_combo = ttk.Combobox(lang_group, textvariable=language_var, state='readonly')
        language_combo['values'] = ['English', 'German', 'French', 'Spanish']
        language_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['general']['language'] = language_var
        
        # Date format
        ttk.Label(lang_group, text="Date format:").grid(row=1, column=0, sticky='w', pady=2)
        date_format_var = tk.StringVar(value=self.settings.general.date_format)
        date_format_combo = ttk.Combobox(lang_group, textvariable=date_format_var, state='readonly')
        date_format_combo['values'] = ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']
        date_format_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.tabs['general']['date_format'] = date_format_var
    
    def browse_directory(self, var: tk.StringVar):
        """Browse for a directory and update the variable."""
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)
    
    def capture_shortcut(self, var: tk.StringVar):
        """Capture a keyboard shortcut."""
        # Create a simple capture dialog
        capture_dialog = tk.Toplevel(self.dialog)
        capture_dialog.title("Capture Shortcut")
        capture_dialog.geometry("300x150")
        capture_dialog.transient(self.dialog)
        capture_dialog.grab_set()
        
        ttk.Label(capture_dialog, text="Press the desired key combination:", 
                 font=('Arial', 12)).pack(pady=20)
        
        result_label = ttk.Label(capture_dialog, text="", 
                               font=('Arial', 10, 'bold'))
        result_label.pack(pady=10)
        
        captured_key = tk.StringVar()
        
        def on_key_press(event):
            # Build key combination string
            modifiers = []
            if event.state & 0x4:  # Ctrl
                modifiers.append('Ctrl')
            if event.state & 0x8:  # Alt
                modifiers.append('Alt')
            if event.state & 0x1:  # Shift
                modifiers.append('Shift')
            
            key = event.keysym
            if key not in ['Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R']:
                if modifiers:
                    shortcut = '+'.join(modifiers) + '+' + key
                else:
                    shortcut = key
                captured_key.set(shortcut)
                result_label.config(text=f"Captured: {shortcut}")
        
        capture_dialog.bind('<KeyPress>', on_key_press)
        capture_dialog.focus_set()
        
        button_frame = ttk.Frame(capture_dialog)
        button_frame.pack(pady=10)
        
        def accept_shortcut():
            if captured_key.get():
                var.set(captured_key.get())
            capture_dialog.destroy()
        
        ttk.Button(button_frame, text="Accept", command=accept_shortcut).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=capture_dialog.destroy).pack(side='left', padx=5)
    
    def create_manual_backup(self):
        """Create a manual backup."""
        if self.backup_manager:
            try:
                backup_path = self.backup_manager.create_backup('manual')
                if backup_path:
                    messagebox.showinfo("Backup Created", f"Backup created successfully:\n{backup_path}")
                else:
                    messagebox.showerror("Backup Failed", "Failed to create backup.")
            except Exception as e:
                messagebox.showerror("Backup Error", f"Error creating backup:\n{str(e)}")
        else:
            messagebox.showwarning("Backup Unavailable", "Backup manager is not available.")
    
    def show_backup_list(self):
        """Show a list of available backups."""
        if not self.backup_manager:
            messagebox.showwarning("Backup Unavailable", "Backup manager is not available.")
            return
        
        # Create backup list dialog
        backup_dialog = tk.Toplevel(self.dialog)
        backup_dialog.title("Available Backups")
        backup_dialog.geometry("600x400")
        backup_dialog.transient(self.dialog)
        
        # Create treeview for backup list
        columns = ('Name', 'Type', 'Size', 'Created')
        tree = ttk.Treeview(backup_dialog, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(backup_dialog, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Load backup list
        try:
            backups = self.backup_manager.get_backup_list()
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024) if backup['size'] else 0
                tree.insert('', 'end', values=(
                    backup['name'],
                    backup.get('backup_type', 'Unknown'),
                    f"{size_mb:.1f} MB",
                    backup['created'].strftime('%Y-%m-%d %H:%M')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Error loading backup list:\n{str(e)}")
    
    def apply_settings(self):
        """Apply the current settings without closing the dialog."""
        # Prevent concurrent saves
        if self._saving:
            return
            
        try:
            self._saving = True
            
            # Update settings object with current values
            self.update_settings_object()
            
            # Save settings (no parameter needed)
            self.settings_manager.save_settings()
            
            # Refresh our reference to settings after save
            self.settings = self.settings_manager.settings
            
            # Apply theme to settings dialog immediately if theme changed
            if self.theme_manager and 'appearance' in self.tabs:
                new_theme = self.tabs['appearance']['theme'].get()
                if new_theme != self.theme_manager.current_theme:
                    # Apply theme to main window through callback first
                    if self.on_settings_changed:
                        self.on_settings_changed(self.settings)
                    # Now apply to this dialog window
                    self.apply_theme_to_dialog(new_theme)
                else:
                    # Theme unchanged, just notify parent
                    if self.on_settings_changed:
                        self.on_settings_changed(self.settings)
            else:
                # No theme manager or appearance tab, just notify parent
                if self.on_settings_changed:
                    self.on_settings_changed(self.settings)
            
            self.theme_applied = True
            
            messagebox.showinfo("Settings Applied", "Settings have been applied successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error applying settings:\n{str(e)}")
        finally:
            self._saving = False
    
    def save_settings(self):
        """Save the current settings without showing confirmation message.
        
        Note: This is an internal method. UI buttons use apply_settings() or ok_settings().
        Kept for internal use and potential future programmatic settings saves.
        """
        # Prevent concurrent saves
        if self._saving:
            return
            
        try:
            self._saving = True
            
            # Update settings object with current values
            self.update_settings_object()
            
            # Save settings (no parameter needed)
            self.settings_manager.save_settings()
            
            # Refresh our reference to settings after save
            self.settings = self.settings_manager.settings
            
            # Notify parent of changes
            if self.on_settings_changed:
                self.on_settings_changed(self.settings)
            self.theme_applied = True
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings:\n{str(e)}")
        finally:
            self._saving = False
    
    def ok_settings(self):
        """Apply settings and close the dialog."""
        try:
            self.apply_settings()
            self.dialog.destroy()
        except:
            pass  # Error already shown in apply_settings
    
    def cancel_settings(self):
        """Cancel changes and close the dialog."""
        # Restore original theme if it was changed
        if (self.theme_manager and self.initial_theme and not self.theme_applied and
                self.theme_manager.current_theme != self.initial_theme):
            self.theme_manager.apply_theme(self.initial_theme)
        
        self.dialog.destroy()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        if messagebox.askyesno("Reset Settings", 
                              "Are you sure you want to reset all settings to default values?\n"
                              "This action cannot be undone."):
            try:
                # Create default settings
                default_settings = UserSettings()
                
                # Update all UI elements with default values
                self.update_ui_with_settings(default_settings)
                
                messagebox.showinfo("Settings Reset", "All settings have been reset to default values.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error resetting settings:\n{str(e)}")
    
    def import_settings(self):
        """Import settings from a file."""
        file_path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                imported_settings = self.settings_manager.import_settings(file_path)
                if imported_settings:
                    self.update_ui_with_settings(imported_settings)
                    messagebox.showinfo("Settings Imported", "Settings have been imported successfully.")
                else:
                    messagebox.showerror("Import Failed", "Failed to import settings from file.")
            except Exception as e:
                messagebox.showerror("Import Error", f"Error importing settings:\n{str(e)}")
    
    def export_settings(self):
        """Export current settings to a file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Update settings object with current UI values
                self.update_settings_object()
                
                success = self.settings_manager.export_settings(self.settings, file_path)
                if success:
                    messagebox.showinfo("Settings Exported", f"Settings have been exported to:\n{file_path}")
                else:
                    messagebox.showerror("Export Failed", "Failed to export settings.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting settings:\n{str(e)}")
    
    def update_settings_object(self):
        """Update the settings object with current UI values."""
        # Work norms
        if 'work_norms' in self.tabs:
            wn = self.tabs['work_norms']
            self.settings.work_norms.daily_work_hours = wn['daily_work_hours'].get()
            self.settings.work_norms.max_break_duration = wn['max_break_duration'].get()
            self.settings.work_norms.max_daily_break_time = wn['daily_break_limit'].get()
            self.settings.work_norms.overtime_threshold = wn['overtime_threshold'].get()
            # Note: warning_threshold is not stored as it's derived from overtime_threshold
        
        # Appearance
        if 'appearance' in self.tabs:
            ap = self.tabs['appearance']
            # Convert theme string back to Theme enum
            theme_value = ap['theme'].get()
            from core.settings import Theme
            for theme_enum in Theme:
                if theme_enum.value == theme_value:
                    self.settings.appearance.theme = theme_enum
                    break
            # Font settings
            if 'font_family' in ap:
                self.settings.appearance.font_family = ap['font_family'].get()
            if 'font_size' in ap:
                self.settings.appearance.font_size = ap['font_size'].get()
            # Window settings
            if 'window_width' in ap:
                self.settings.appearance.window_width = ap['window_width'].get()
            if 'window_height' in ap:
                self.settings.appearance.window_height = ap['window_height'].get()
            if 'window_maximized' in ap:
                self.settings.appearance.window_maximized = ap['window_maximized'].get()
            self.settings.appearance.remember_window_position = ap['remember_position'].get()
            self.settings.appearance.remember_window_position = ap['remember_size'].get()
        
        # Notifications
        if 'notifications' in self.tabs:
            nt = self.tabs['notifications']
            self.settings.notifications.enabled = nt['enabled'].get()
            self.settings.notifications.system_notifications = nt['system_notifications'].get()
            self.settings.notifications.work_start_reminder = nt['work_start_reminder'].get()
            self.settings.notifications.work_start_time = nt['work_start_time'].get()
            self.settings.notifications.break_reminders = nt['break_reminder'].get()
            self.settings.notifications.break_reminder_interval = nt['break_reminder_interval'].get()
            self.settings.notifications.overtime_warnings = nt['overtime_warning'].get()
            self.settings.notifications.end_day_reminder = nt['end_day_reminder'].get()
            self.settings.notifications.end_day_time = nt['end_day_time'].get()
        
        # Backup
        if 'backup' in self.tabs:
            bp = self.tabs['backup']
            self.settings.backup.auto_backup = bp['auto_backup_enabled'].get()
            self.settings.backup.backup_frequency = bp['backup_frequency'].get()
            # Note: backup_time not stored in settings yet
            self.settings.backup.backup_location = bp['backup_directory'].get()
            # Note: max_backup_files not stored in settings yet
            self.settings.backup.backup_retention_days = bp['retention_days'].get()
            self.settings.backup.compress_backups = bp['compress_backups'].get()
            self.settings.backup.backup_on_exit = bp['backup_on_exit'].get()
        
        # Shortcuts
        if 'shortcuts' in self.tabs:
            sc = self.tabs['shortcuts']
            self.settings.shortcuts.start_work = sc['start_work'].get()
            self.settings.shortcuts.end_work = sc['end_work'].get()
            self.settings.shortcuts.take_break = sc['take_break'].get()
            self.settings.shortcuts.end_break = sc['end_break'].get()
            self.settings.shortcuts.show_summary = sc['show_summary'].get()
            self.settings.shortcuts.export_data = sc['export_data'].get()
            self.settings.shortcuts.settings = sc['settings'].get()
            self.settings.shortcuts.quit_app = sc['quit_app'].get()
        
        # General
        if 'general' in self.tabs:
            gn = self.tabs['general']
            self.settings.general.start_minimized = gn['start_minimized'].get()
            self.settings.general.auto_start_work_on_open = gn['auto_start_work'].get()
            self.settings.general.system_tray_enabled = gn['system_tray_enabled'].get()
            self.settings.general.minimize_to_tray = gn['minimize_to_tray'].get()
            self.settings.general.confirm_exit = gn['confirm_exit'].get()
            self.settings.general.save_on_exit = gn['save_on_exit'].get()
            self.settings.general.language = gn['language'].get()
            self.settings.general.date_format = gn['date_format'].get()
    
    def update_ui_with_settings(self, settings: UserSettings):
        """Update UI elements with the provided settings."""
        self.settings = settings
        
        # Work norms
        if 'work_norms' in self.tabs:
            wn = self.tabs['work_norms']
            wn['daily_work_hours'].set(settings.work_norms.daily_work_hours)
            wn['max_break_duration'].set(settings.work_norms.max_break_duration)
            wn['daily_break_limit'].set(settings.work_norms.max_daily_break_time)
            wn['overtime_threshold'].set(settings.work_norms.overtime_threshold)
            wn['warning_threshold'].set(settings.work_norms.overtime_threshold - 0.5)
        
        # Appearance
        if 'appearance' in self.tabs:
            ap = self.tabs['appearance']
            # Handle theme value - convert enum to string if necessary
            theme_value = settings.appearance.theme
            if hasattr(theme_value, 'value'):
                theme_value = theme_value.value
            ap['theme'].set(theme_value)
            # Font settings
            if 'font_family' in ap:
                ap['font_family'].set(settings.appearance.font_family)
            if 'font_size' in ap:
                ap['font_size'].set(settings.appearance.font_size)
            # Window settings
            if 'window_width' in ap:
                ap['window_width'].set(settings.appearance.window_width)
            if 'window_height' in ap:
                ap['window_height'].set(settings.appearance.window_height)
            if 'window_maximized' in ap:
                ap['window_maximized'].set(settings.appearance.window_maximized)
            ap['remember_position'].set(settings.appearance.remember_window_position)
            ap['remember_size'].set(settings.appearance.remember_window_position)
        
        # Notifications
        if 'notifications' in self.tabs:
            nt = self.tabs['notifications']
            nt['enabled'].set(settings.notifications.enabled)
            nt['system_notifications'].set(settings.notifications.system_notifications)
            nt['work_start_reminder'].set(settings.notifications.work_start_reminder)
            nt['work_start_time'].set(settings.notifications.work_start_time)
            nt['break_reminder'].set(settings.notifications.break_reminders)
            nt['break_reminder_interval'].set(settings.notifications.break_reminder_interval)
            nt['overtime_warning'].set(settings.notifications.overtime_warnings)
            nt['end_day_reminder'].set(settings.notifications.end_day_reminder)
            nt['end_day_time'].set(settings.notifications.end_day_time)
        
        # Backup
        if 'backup' in self.tabs:
            bp = self.tabs['backup']
            bp['auto_backup_enabled'].set(settings.backup.auto_backup)
            bp['backup_frequency'].set(settings.backup.backup_frequency)
            bp['backup_time'].set("23:00")  # Default backup time
            bp['backup_directory'].set(settings.backup.backup_location)
            bp['max_backup_files'].set(10)  # Default max backup files
            bp['retention_days'].set(settings.backup.backup_retention_days)
            bp['compress_backups'].set(settings.backup.compress_backups)
            bp['backup_on_exit'].set(settings.backup.backup_on_exit)
        
        # Shortcuts
        if 'shortcuts' in self.tabs:
            sc = self.tabs['shortcuts']
            sc['start_work'].set(settings.shortcuts.start_work)
            sc['end_work'].set(settings.shortcuts.end_work)
            sc['take_break'].set(settings.shortcuts.take_break)
            sc['end_break'].set(settings.shortcuts.end_break)
            sc['show_summary'].set(settings.shortcuts.show_summary)
            sc['export_data'].set(settings.shortcuts.export_data)
            sc['settings'].set(settings.shortcuts.settings)
            sc['quit_app'].set(settings.shortcuts.quit_app)
        
        # General
        if 'general' in self.tabs:
            gn = self.tabs['general']
            gn['start_minimized'].set(settings.general.start_minimized)
            gn['auto_start_work'].set(settings.general.auto_start_work_on_open)
            gn['system_tray_enabled'].set(settings.general.system_tray_enabled)
            gn['minimize_to_tray'].set(settings.general.minimize_to_tray)
            gn['confirm_exit'].set(settings.general.confirm_exit)
            gn['save_on_exit'].set(settings.general.save_on_exit)
            gn['language'].set(settings.general.language)
            gn['date_format'].set(settings.general.date_format)
    
    def apply_theme_to_dialog(self, theme_name: str):
        """Apply theme colors to all widgets in the settings dialog.
        
        Args:
            theme_name: Name of the theme to apply
        """
        if not self.theme_manager:
            return
        
        # Get theme colors
        colors = self.theme_manager.get_theme_colors(theme_name)
        
        # Apply to dialog window
        try:
            self.dialog.configure(bg=colors['bg_primary'])
        except:
            pass
        
        # Recursively apply to all child widgets
        self._apply_theme_recursive(self.dialog, colors)
        
        # Force update
        self.dialog.update_idletasks()
    
    def _apply_theme_recursive(self, widget, colors: dict):
        """Recursively apply theme to a widget and its children.
        
        Args:
            widget: The widget to theme
            colors: Dictionary of theme colors
        """
        try:
            # Determine widget type and apply appropriate styling
            widget_class = widget.winfo_class()
            
            # Handle tk widgets
            if widget_class in ('Frame', 'Toplevel'):
                widget.configure(bg=colors['bg_primary'])
            elif widget_class == 'Label':
                widget.configure(bg=colors['bg_primary'], fg=colors['fg_primary'])
            elif widget_class == 'Button':
                widget.configure(
                    bg=colors['button_bg'],
                    fg=colors['button_fg'],
                    activebackground=colors['button_active'],
                    activeforeground=colors['button_fg']
                )
            elif widget_class == 'Entry':
                widget.configure(
                    bg=colors['entry_bg'],
                    fg=colors['entry_fg'],
                    insertbackground=colors['fg_primary']
                )
            elif widget_class == 'Text':
                widget.configure(
                    bg=colors['bg_secondary'],
                    fg=colors['fg_primary'],
                    insertbackground=colors['fg_primary']
                )
            elif widget_class == 'Listbox':
                widget.configure(
                    bg=colors['bg_secondary'],
                    fg=colors['fg_primary']
                )
            elif widget_class == 'Canvas':
                widget.configure(bg=colors['bg_primary'])
            elif widget_class in ('TFrame', 'TLabelframe'):
                # ttk widgets use styles, but we can set background
                try:
                    widget.configure(style='Themed.TFrame')
                except:
                    pass
            
            # Recursively process children
            for child in widget.winfo_children():
                self._apply_theme_recursive(child, colors)
                
        except Exception as e:
            # Silently ignore widgets that can't be configured
            pass