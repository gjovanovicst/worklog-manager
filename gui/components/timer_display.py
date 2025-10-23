"""Timer display component for real-time time tracking."""

import tkinter as tk
from tkinter import ttk
import logging

from data.models import TimeCalculation, WorklogState
from core.time_calculator import TimeCalculator


class TimerDisplay(ttk.Frame):
    """Component for displaying real-time work time information."""
    
    def __init__(self, parent, settings_manager=None):
        """Initialize the timer display.
        
        Args:
            parent: Parent widget
            settings_manager: Settings manager for work norms
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        self.time_calculator = TimeCalculator(settings_manager)
        self.theme_manager = None
        
        zero_time = self.time_calculator.format_duration_with_seconds(0)
        norm_time = self.time_calculator.format_duration_with_seconds(
            self.time_calculator.WORK_NORM_MINUTES * 60
        )

        # Create variables for time displays
        self.current_session_var = tk.StringVar(value=zero_time)
        self.total_work_var = tk.StringVar(value=zero_time)
        self.break_time_var = tk.StringVar(value=zero_time)
        self.productive_time_var = tk.StringVar(value=zero_time)
        self.remaining_var = tk.StringVar(value=norm_time)
        self.overtime_var = tk.StringVar(value=zero_time)
        
        # Store reference to widgets that need theming
        self.current_frame = None
        self.current_session_label_widget = None
        self.current_session_title_label = None
        self.total_work_title_label = None
        self.total_work_label = None
        self.break_time_title_label = None
        self.break_time_label = None
        self.productive_time_title_label = None
        self.productive_time_label = None
        self.remaining_title_label = None
        self.remaining_label = None
        self.overtime_title_label = None
        self.overtime_label = None

        self._create_widgets()
    
    def _get_font_config(self, size_modifier=0, bold=False):
        """Get font configuration from settings.
        
        Args:
            size_modifier: Amount to add/subtract from base font size
            bold: Whether to make the font bold
            
        Returns:
            tuple: Font configuration (family, size, weight)
        """
        if self.settings_manager:
            font_family = self.settings_manager.settings.appearance.font_family
            font_size = self.settings_manager.settings.appearance.font_size + size_modifier
        else:
            # Fallback to defaults
            font_family = "Arial"
            font_size = 10 + size_modifier
        
        if bold:
            return (font_family, font_size, "bold")
        return (font_family, font_size)
    
    def update_settings_manager(self, settings_manager):
        """Update the settings manager and time calculator."""
        self.settings_manager = settings_manager
        self.time_calculator = TimeCalculator(settings_manager)
        # Update fonts when settings change
        self._update_fonts()
    
    def _update_fonts(self):
        """Update fonts in all labels based on current settings."""
        try:
            # Update current session label
            if hasattr(self, 'current_session_label_widget'):
                self.current_session_label_widget.config(font=self._get_font_config(size_modifier=2, bold=True))
            
            # Update value labels
            if hasattr(self, 'total_work_label'):
                self.total_work_label.config(font=self._get_font_config(size_modifier=-1, bold=True))
            if hasattr(self, 'break_time_label'):
                self.break_time_label.config(font=self._get_font_config(size_modifier=-1, bold=True))
            if hasattr(self, 'productive_time_label'):
                self.productive_time_label.config(font=self._get_font_config(size_modifier=-1, bold=True))
            if hasattr(self, 'remaining_label'):
                self.remaining_label.config(font=self._get_font_config(size_modifier=-1, bold=True))
            if hasattr(self, 'overtime_label'):
                self.overtime_label.config(font=self._get_font_config(size_modifier=-1, bold=True))
                
        except Exception as e:
            self.logger.error(f"Error updating fonts: {e}")
    
    def _create_widgets(self):
        """Create and layout the timer display widgets."""
        # Main frame with border
        main_frame = ttk.LabelFrame(self, text="Time Summary", padding="10")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create a grid layout for time displays
        row = 0
        
        # Current session time (highlighted)
        self.current_frame = tk.Frame(main_frame, relief="ridge", bd=1)
        self.current_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.current_frame.columnconfigure(1, weight=1)
        
        self.current_session_title_label = tk.Label(self.current_frame, text="Current Session:", 
                font=self._get_font_config(bold=True))
        self.current_session_title_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.current_session_label_widget = tk.Label(self.current_frame, textvariable=self.current_session_var,
                                            font=self._get_font_config(size_modifier=2, bold=True))
        self.current_session_label_widget.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        
        row += 1
        
        # Total work time
        self.total_work_title_label = tk.Label(main_frame, text="Total Work Time:", 
                font=self._get_font_config(size_modifier=-1))
        self.total_work_title_label.grid(row=row, column=0, sticky="w", pady=2)
        
        self.total_work_label = tk.Label(main_frame, textvariable=self.total_work_var,
                                       font=self._get_font_config(size_modifier=-1, bold=True))
        self.total_work_label.grid(row=row, column=1, sticky="e", pady=2)
        
        row += 1
        
        # Break time
        self.break_time_title_label = tk.Label(main_frame, text="Break Time:", 
                font=self._get_font_config(size_modifier=-1))
        self.break_time_title_label.grid(row=row, column=0, sticky="w", pady=2)
        
        self.break_time_label = tk.Label(main_frame, textvariable=self.break_time_var,
                                       font=self._get_font_config(size_modifier=-1, bold=True))
        self.break_time_label.grid(row=row, column=1, sticky="e", pady=2)
        
        row += 1
        
        # Productive time
        self.productive_time_title_label = tk.Label(main_frame, text="Productive Time:", 
                font=self._get_font_config(size_modifier=-1))
        self.productive_time_title_label.grid(row=row, column=0, sticky="w", pady=2)
        
        self.productive_time_label = tk.Label(main_frame, textvariable=self.productive_time_var,
                                            font=self._get_font_config(size_modifier=-1, bold=True))
        self.productive_time_label.grid(row=row, column=1, sticky="e", pady=2)
        
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, columnspan=2, 
                                                           sticky="ew", pady=5)
        row += 1
        
        # Remaining time
        self.remaining_title_label = tk.Label(main_frame, text="Remaining:", 
                font=self._get_font_config(size_modifier=-1))
        self.remaining_title_label.grid(row=row, column=0, sticky="w", pady=2)
        
        self.remaining_label = tk.Label(main_frame, textvariable=self.remaining_var,
                                      font=self._get_font_config(size_modifier=-1, bold=True))
        self.remaining_label.grid(row=row, column=1, sticky="e", pady=2)
        
        row += 1
        
        # Overtime
        self.overtime_title_label = tk.Label(main_frame, text="Overtime:", 
                font=self._get_font_config(size_modifier=-1))
        self.overtime_title_label.grid(row=row, column=0, sticky="w", pady=2)
        
        self.overtime_label = tk.Label(main_frame, textvariable=self.overtime_var,
                                     font=self._get_font_config(size_modifier=-1, bold=True))
        self.overtime_label.grid(row=row, column=1, sticky="e", pady=2)
        
        # Configure column weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def update_display(self, calculations: TimeCalculation, current_session_seconds: int = 0):
        """Update the timer display with new calculations.
        
        Args:
            calculations: TimeCalculation object with current metrics
            current_session_seconds: Current session time in seconds
        """
        try:
            # Update current session time
            current_session_str = self.time_calculator.format_duration_with_seconds(current_session_seconds)
            self.current_session_var.set(current_session_str)
            
            # Update work times
            self.total_work_var.set(
                self.time_calculator.format_duration_with_seconds(calculations.total_work_seconds)
            )
            self.break_time_var.set(
                self.time_calculator.format_duration_with_seconds(calculations.total_break_seconds)
            )
            self.productive_time_var.set(
                self.time_calculator.format_duration_with_seconds(calculations.productive_seconds)
            )
            self.remaining_var.set(
                self.time_calculator.format_duration_with_seconds(calculations.remaining_seconds)
            )
            self.overtime_var.set(
                self.time_calculator.format_duration_with_seconds(calculations.overtime_seconds)
            )
            
            # Update colors based on status
            self._update_colors(calculations)
            
        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")
    
    def _update_colors(self, calculations: TimeCalculation):
        """Update label colors based on work status.
        
        Args:
            calculations: TimeCalculation object
        """
        normal_color, warning_color, overtime_color, good_color = self._get_status_palette()
        
        # Productive time color
        if calculations.is_overtime:
            self.productive_time_label.config(fg=overtime_color)
            self.overtime_label.config(fg=overtime_color)
        elif calculations.productive_minutes >= calculations.work_norm_minutes * 0.9:  # 90% of norm
            self.productive_time_label.config(fg=good_color)
            self.overtime_label.config(fg=normal_color)
        elif calculations.productive_minutes >= calculations.work_norm_minutes * 0.7:  # 70% of norm
            self.productive_time_label.config(fg=warning_color)
            self.overtime_label.config(fg=normal_color)
        else:
            self.productive_time_label.config(fg=normal_color)
            self.overtime_label.config(fg=normal_color)
        
        # Remaining time color
        if calculations.remaining_minutes == 0:
            self.remaining_label.config(fg=good_color)
        elif calculations.remaining_minutes <= 60:  # Less than 1 hour remaining
            self.remaining_label.config(fg=warning_color)
        else:
            self.remaining_label.config(fg=normal_color)
    
    def reset_display(self):
        """Reset all displays to zero."""
        zero_time = self.time_calculator.format_duration_with_seconds(0)
        norm_time = self.time_calculator.format_duration_with_seconds(
            self.time_calculator.WORK_NORM_MINUTES * 60
        )

        self.current_session_var.set(zero_time)
        self.total_work_var.set(zero_time)
        self.break_time_var.set(zero_time)
        self.productive_time_var.set(zero_time)
        self.remaining_var.set(norm_time)
        self.overtime_var.set(zero_time)
        
        # Reset colors
        normal_color, _, _, _ = self._get_status_palette()
        self.productive_time_label.config(fg=normal_color)
        self.remaining_label.config(fg=normal_color)
        self.overtime_label.config(fg=normal_color)
    
    def register_with_theme_manager(self, theme_manager):
        """Register widgets with the theme manager for theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        if theme_manager:
            self.theme_manager = theme_manager
            self.logger.debug("Registering TimerDisplay widgets with theme manager")
            # Register the current session frame with a highlighted background
            if self.current_frame:
                theme_manager.register_widget(self.current_frame, 'highlighted_bg')
            
            # Register the current session labels
            if self.current_session_title_label:
                theme_manager.register_widget(self.current_session_title_label, 'highlighted_label')
            
            if self.current_session_label_widget:
                theme_manager.register_widget(self.current_session_label_widget, 'highlighted_accent_label')
            
            # Register all title labels
            if self.total_work_title_label:
                theme_manager.register_widget(self.total_work_title_label, 'label')
            if self.break_time_title_label:
                theme_manager.register_widget(self.break_time_title_label, 'label')
            if self.productive_time_title_label:
                theme_manager.register_widget(self.productive_time_title_label, 'label')
            if self.remaining_title_label:
                theme_manager.register_widget(self.remaining_title_label, 'label')
            if self.overtime_title_label:
                theme_manager.register_widget(self.overtime_title_label, 'label')
            
            # Register all value labels
            if self.total_work_label:
                theme_manager.register_widget(self.total_work_label, 'label')
            if self.break_time_label:
                theme_manager.register_widget(self.break_time_label, 'label')
            if self.productive_time_label:
                theme_manager.register_widget(self.productive_time_label, 'label')
            if self.remaining_label:
                theme_manager.register_widget(self.remaining_label, 'label')
            if self.overtime_label:
                theme_manager.register_widget(self.overtime_label, 'label')
            
            self.logger.debug("TimerDisplay widgets registered successfully")

    def _get_status_palette(self):
        """Resolve the status colors from the active theme."""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            return (
                colors.get('fg_primary', '#000000'),
                colors.get('warning', '#FF8C00'),
                colors.get('danger', '#DC143C'),
                colors.get('success', '#006400')
            )

        # Fallback palette when theming is unavailable
        return ('#000000', '#FF8C00', '#DC143C', '#006400')
