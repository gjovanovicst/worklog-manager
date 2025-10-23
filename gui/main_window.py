"""Main application window for the Worklog Manager."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
import logging
from pathlib import Path

from core.worklog_manager import WorklogManager
from core.settings import SettingsManager
from gui.theme_manager import ThemeManager
from core.simple_backup_manager import BackupManager
from data.models import WorklogState, ActionType, BreakType
from gui.components.timer_display import TimerDisplay
from gui.components.break_tracker import BreakTracker
from gui.dialogs.revoke_dialog import show_revoke_dialog


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize core managers
        self.settings_manager = SettingsManager()
        self.worklog_manager = WorklogManager(settings_manager=self.settings_manager)
        
        # Initialize backup manager
        try:
            self.backup_manager = BackupManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize backup manager: {e}")
            self.backup_manager = None

        # System tray manager reference (wired up by main application)
        self.system_tray_manager = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Worklog Manager v1.7.0")
        
        # Load window settings from configuration
        appearance_settings = self.settings_manager.settings.appearance
        window_width = appearance_settings.window_width
        window_height = appearance_settings.window_height
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        
        # Withdraw window initially to prevent flash during setup
        self.root.withdraw()
        
        # Get saved theme before initializing theme manager
        saved_theme = self.settings_manager.settings.appearance.theme
        if hasattr(saved_theme, 'value'):
            saved_theme = saved_theme.value
        
        # Initialize theme manager with the saved theme to avoid light theme flash
        try:
            self.theme_manager = ThemeManager(self.root, initial_theme=saved_theme)
            
            # Immediately apply background color to prevent black flash
            if self.theme_manager:
                colors = self.theme_manager.get_theme_colors(saved_theme)
                self.root.configure(bg=colors['bg_primary'])
                self.root.update_idletasks()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize theme manager: {e}")
            self.theme_manager = None
        
        # Track window visibility state for theme reapplication
        self._window_was_hidden = False
        self._last_window_state = None
        self._state_check_scheduled = False
        
        # Don't apply theme yet - wait until all widgets are created
        # Just configure initial font settings
        if self.theme_manager:
            # Apply initial fonts
            try:
                font_family = self.settings_manager.settings.appearance.font_family
                font_size = self.settings_manager.settings.appearance.font_size
                self.logger.info(f"Applying initial fonts: {font_family} {font_size}pt")
                self.theme_manager.apply_fonts(font_family, font_size)
            except Exception as e:
                self.logger.error(f"Failed to apply initial fonts: {e}")
        
        # Set minimum size
        self.root.minsize(550, 450)
        
        # Apply window position if remember_window_position is enabled
        if appearance_settings.remember_window_position:
            window_x = appearance_settings.window_x
            window_y = appearance_settings.window_y
            self.root.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
        else:
            # Center the window
            self._center_window()
        
        # Track last known normal geometry for tray restore
        self._saved_geometry = self.root.geometry()

        # Don't apply maximized or minimized state yet - do it after theme is applied
        # Track maximize state for system tray restore
        self._was_maximized = appearance_settings.window_maximized
        self.root.bind("<Configure>", self._on_window_configure)
        
        # Bind to window visibility changes to reapply theme on restore
        self.root.bind("<Map>", self._on_window_mapped)
        self.root.bind("<Unmap>", self._on_window_unmapped)
        
        # Start monitoring window state for minimize/restore
        self._start_state_monitoring()

        # Variables for break type selection
        self.break_type_var = tk.StringVar(value=BreakType.GENERAL.value)
        
        # Create widgets
        self._create_widgets()
        
        # Register widgets with theme manager
        self._register_widgets_with_theme_manager()
        
        # Apply theme after widgets are registered to ensure all widgets get themed
        if self.theme_manager:
            try:
                current_theme = self.settings_manager.settings.appearance.theme
                if hasattr(current_theme, 'value'):
                    current_theme = current_theme.value
                self.logger.info(f"Applying theme '{current_theme}' after widget registration")
                self.theme_manager.apply_theme(current_theme)
                
                # Force immediate UI update
                self.root.update_idletasks()
                
                # Apply theme again after a short delay to catch any stragglers
                self.root.after(100, lambda: self._apply_theme_deferred(current_theme))
            except Exception as e:
                self.logger.error(f"Failed to apply theme after widget registration: {e}")

        # Set up timer callback
        self.worklog_manager.set_timer_callback(self._timer_update)
        
        # Initial update
        self._update_display()
        
        # Setup window closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Show window after everything is set up and themed
        # The window was withdrawn at startup to prevent flash
        general_settings = self.settings_manager.settings.general
        
        if general_settings.start_minimized:
            # If starting minimized, iconify instead of deiconify
            self.root.deiconify()  # First deiconify to normal
            self.root.iconify()    # Then iconify to minimize
        else:
            # Show the window normally
            self.root.deiconify()
            
            # Apply maximized state if needed (after deiconify)
            if appearance_settings.window_maximized:
                self.root.state('zoomed')
    
    def _get_font_config(self, size_modifier=0, bold=False):
        """Get font configuration from settings.
        
        Args:
            size_modifier: Amount to add/subtract from base font size
            bold: Whether to make the font bold
            
        Returns:
            tuple: Font configuration (family, size, weight)
        """
        font_family = self.settings_manager.settings.appearance.font_family
        font_size = self.settings_manager.settings.appearance.font_size + size_modifier
        if bold:
            return (font_family, font_size, "bold")
        return (font_family, font_size)
    
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Scrollable container to accommodate smaller window sizes
        self.content_container = ttk.Frame(self.root, style="Themed.TFrame")
        self.content_container.pack(fill="both", expand=True)

        canvas_bg = self.root.cget("bg") if self.root else None

        self.scroll_canvas = tk.Canvas(
            self.content_container,
            highlightthickness=0,
            borderwidth=0,
            background=canvas_bg
        )
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.vertical_scrollbar = ttk.Scrollbar(
            self.content_container,
            orient="vertical",
            command=self.scroll_canvas.yview
        )
        self.vertical_scrollbar.pack(side="right", fill="y")

        self._scrollbar_visible = True

        self.scroll_canvas.configure(yscrollcommand=self.vertical_scrollbar.set)

        # Main content frame hosted inside the canvas
        self.main_frame = ttk.Frame(self.scroll_canvas, padding="10", style="Themed.TFrame")
        self._canvas_window_id = self.scroll_canvas.create_window(
            (0, 0), window=self.main_frame, anchor="nw"
        )

        # Ensure scrollbar updates whenever content changes size
        self.main_frame.bind("<Configure>", self._on_canvas_frame_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)

        # Support mouse wheel scrolling
        self._bind_mousewheel(self.scroll_canvas)
        self._bind_mousewheel(self.main_frame)
        
        # Header section
        self._create_header(self.main_frame)
        
        # Control buttons section
        self._create_control_buttons(self.main_frame)
        
        # Break type selection
        self._create_break_selection(self.main_frame)
        
        # Timer display component
        self.timer_display = TimerDisplay(self.main_frame, self.settings_manager)
        self.timer_display.pack(fill="x", pady=10)
        
        # Break tracker
        self.break_tracker = BreakTracker(self.main_frame)
        self.break_tracker.pack(fill="both", expand=True, pady=10)
        
        # Action buttons section
        self._create_action_buttons(self.main_frame)
    
    def _register_widgets_with_theme_manager(self):
        """Register all main window widgets with the theme manager for theme updates."""
        if not self.theme_manager:
            return
            
        try:
            # Register tkinter widgets that need theme updates
            if hasattr(self, 'scroll_canvas'):
                self.theme_manager.register_widget(self.scroll_canvas, 'primary_bg')

            if hasattr(self, 'date_label'):
                self.theme_manager.register_widget(self.date_label, 'primary_bg')
            
            if hasattr(self, 'status_label'):
                self.theme_manager.register_widget(self.status_label, 'primary_bg')
            
            # Register timer display and break tracker if they have theme registration methods
            if hasattr(self.timer_display, 'register_with_theme_manager'):
                self.timer_display.register_with_theme_manager(self.theme_manager)
            
            if hasattr(self.break_tracker, 'register_with_theme_manager'):
                self.break_tracker.register_with_theme_manager(self.theme_manager)
                
            self.logger.info("Registered main window widgets with theme manager")
                
        except Exception as e:
            self.logger.error(f"Error registering widgets with theme manager: {e}")
    
    def _apply_theme_deferred(self, theme_name: str):
        """Apply theme with a delay to catch any widgets that weren't ready initially.
        
        Args:
            theme_name: Name of the theme to apply
        """
        if self.theme_manager:
            try:
                self.logger.debug(f"Deferred theme application for '{theme_name}'")
                self.theme_manager.apply_theme(theme_name)
            except Exception as e:
                self.logger.error(f"Error in deferred theme application: {e}")
    
    def _on_window_mapped(self, event):
        """Handle window map event (when window becomes visible).
        
        This ensures the theme is correctly applied when the window is restored
        from minimized/iconified state, preventing theme flickering.
        
        Args:
            event: The Map event
        """
        # Only handle events for the main window, not child widgets
        if event.widget != self.root:
            return
        
        try:
            # Only reapply theme if the window was previously hidden
            if not self._window_was_hidden:
                return
            
            # Reset the flag
            self._window_was_hidden = False
            
            # Check if window was actually minimized/iconified before
            current_state = self.root.state()
            
            # Reapply theme to ensure correct colors after window restore
            if self.theme_manager and current_state in ('normal', 'zoomed'):
                current_theme = self.settings_manager.settings.appearance.theme
                if hasattr(current_theme, 'value'):
                    current_theme = current_theme.value
                
                self.logger.debug(f"Window restored from hidden state - reapplying theme '{current_theme}'")
                
                # Reapply theme immediately
                self.theme_manager.apply_theme(current_theme)
                
                # Force update
                self.root.update_idletasks()
                
        except Exception as e:
            self.logger.debug(f"Error in window map handler: {e}")
    
    def _on_window_unmapped(self, event):
        """Handle window unmap event (when window becomes hidden).
        
        Sets a flag to track that the window was hidden, so we can
        reapply the theme when it becomes visible again.
        
        Args:
            event: The Unmap event
        """
        # Only handle events for the main window, not child widgets
        if event.widget != self.root:
            return
        
        try:
            self._window_was_hidden = True
            self.logger.debug("Window hidden - will reapply theme on restore")
        except Exception as e:
            self.logger.debug(f"Error in window unmap handler: {e}")
    
    def _start_state_monitoring(self):
        """Start monitoring window state changes for minimize/restore detection."""
        self._check_window_state()
    
    def _check_window_state(self):
        """Check for window state changes and reapply theme if restored from minimized."""
        try:
            current_state = self.root.state()
            
            # Check if state changed from 'iconic' (minimized) to 'normal' or 'zoomed'
            if self._last_window_state == 'iconic' and current_state in ('normal', 'zoomed'):
                self.logger.debug(f"Window restored from minimized state - reapplying theme")
                
                # Reapply theme immediately
                if self.theme_manager:
                    current_theme = self.settings_manager.settings.appearance.theme
                    if hasattr(current_theme, 'value'):
                        current_theme = current_theme.value
                    
                    # Apply theme
                    self.theme_manager.apply_theme(current_theme)
                    
                    # Force immediate update
                    self.root.update_idletasks()
            
            # Update last known state
            self._last_window_state = current_state
            
        except Exception as e:
            self.logger.debug(f"Error checking window state: {e}")
        
        # Schedule next check (every 200ms)
        if not self._state_check_scheduled:
            self._state_check_scheduled = True
            self.root.after(200, self._schedule_state_check)
    
    def _schedule_state_check(self):
        """Schedule the next state check."""
        self._state_check_scheduled = False
        self._check_window_state()
    
    def _create_header(self, parent):
        """Create the header section with date and status.
        
        Args:
            parent: Parent widget
        """
        self.header_frame = ttk.Frame(parent, style="Themed.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        # Date display
        today = date.today()
        date_text = today.strftime("%A, %B %d, %Y")
        
        self.date_label = tk.Label(self.header_frame, text=f"Date: {date_text}",
                             font=self._get_font_config(size_modifier=2, bold=True))
        self.date_label.pack(side="left")
        
        # Status display
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.header_frame, textvariable=self.status_var,
                               font=self._get_font_config(size_modifier=2, bold=True))
        self.status_label.pack(side="right")
    
    def _create_control_buttons(self, parent):
        """Create the main control buttons.
        
        Args:
            parent: Parent widget
        """
        button_frame = ttk.Frame(parent, style="Themed.TFrame")
        button_frame.pack(fill="x", pady=10)
        
        # First row - Start Work and End Work
        row1_frame = ttk.Frame(button_frame, style="Themed.TFrame")
        row1_frame.pack(fill="x", pady=(0, 10))

        self.start_day_btn = ttk.Button(
            row1_frame,
            text="Start Work",
            command=self._start_day,
            style="StartDay.TButton",
            width=15
        )
        self.start_day_btn.pack(side="left", padx=(0, 10), ipadx=20, ipady=10)

        self.end_day_btn = ttk.Button(
            row1_frame,
            text="End Work",
            command=self._end_day,
            style="EndDay.TButton",
            width=15
        )
        self.end_day_btn.pack(side="right", padx=(10, 0), ipadx=20, ipady=10)

        # Second row - Take a Break and Resume Work
        row2_frame = ttk.Frame(button_frame, style="Themed.TFrame")
        row2_frame.pack(fill="x")

        self.stop_btn = ttk.Button(
            row2_frame,
            text="Take a Break",
            command=self._stop_work,
            style="Stop.TButton",
            width=15
        )
        self.stop_btn.pack(side="left", padx=(0, 10), ipadx=20, ipady=10)

        self.continue_btn = ttk.Button(
            row2_frame,
            text="Resume Work",
            command=self._continue_work,
            style="Continue.TButton",
            width=15
        )
        self.continue_btn.pack(side="right", padx=(10, 0), ipadx=20, ipady=10)
    
    def _create_break_selection(self, parent):
        """Create break type selection widgets.
        
        Args:
            parent: Parent widget
        """
        break_frame = ttk.LabelFrame(parent, text="Break Type", padding="10", style="Themed.TLabelframe")
        break_frame.pack(fill="x", pady=10)
        
        # Radio buttons for break types
        breaks_inner_frame = ttk.Frame(break_frame, style="Themed.TFrame")
        breaks_inner_frame.pack()
        
        lunch_radio = ttk.Radiobutton(breaks_inner_frame, text="Lunch",
                                     variable=self.break_type_var,
                                     value=BreakType.LUNCH.value)
        lunch_radio.pack(side="left", padx=10)
        
        coffee_radio = ttk.Radiobutton(breaks_inner_frame, text="Coffee",
                                      variable=self.break_type_var,
                                      value=BreakType.COFFEE.value)
        coffee_radio.pack(side="left", padx=10)
        
        general_radio = ttk.Radiobutton(breaks_inner_frame, text="General",
                                       variable=self.break_type_var,
                                       value=BreakType.GENERAL.value)
        general_radio.pack(side="left", padx=10)
    
    def _create_action_buttons(self, parent):
        """Create action buttons at the bottom.
        
        Args:
            parent: Parent widget
        """
        action_frame = ttk.Frame(parent, style="Themed.TFrame")
        action_frame.pack(fill="x", pady=(10, 0))
        
        export_btn = ttk.Button(action_frame, text="Export Data",
                               command=self._export_data,
                               style="Themed.TButton")
        export_btn.pack(side="left", padx=(0, 10))
        
        revoke_btn = ttk.Button(action_frame, text="Revoke Action",
                               command=self._revoke_action,
                               style="Themed.TButton")
        revoke_btn.pack(side="left", padx=10)
        
        reset_btn = ttk.Button(action_frame, text="Reset Day",
                              command=self._reset_day,
                              style="Themed.TButton")
        reset_btn.pack(side="left", padx=10)
        
        settings_btn = ttk.Button(action_frame, text="Settings",
                                 command=self._show_settings,
                                 style="Themed.TButton")
        settings_btn.pack(side="right")

    def _on_canvas_frame_configure(self, event):
        """Update the scrollregion to encompass the entire frame."""
        try:
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            self._update_scrollbar_visibility()
        except tk.TclError:
            pass

    def _on_canvas_configure(self, event):
        """Keep the embedded frame width in sync with the canvas width."""
        try:
            self.scroll_canvas.itemconfig(self._canvas_window_id, width=event.width)

            self.main_frame.update_idletasks()
            required_height = self.main_frame.winfo_reqheight()
            canvas_height = max(event.height, required_height)
            self.scroll_canvas.itemconfig(self._canvas_window_id, height=canvas_height)
            self._update_scrollbar_visibility()
        except tk.TclError:
            pass

    def _on_mousewheel(self, event):
        """Allow mouse wheel scrolling inside the canvas."""
        if not hasattr(self, 'scroll_canvas') or not getattr(self, '_scrollbar_visible', False):
            return
        try:
            delta = event.delta
            if delta == 0 and hasattr(event, 'num') and event.num in (4, 5):
                delta = 120 if event.num == 4 else -120
            self.scroll_canvas.yview_scroll(int(-delta / 120), "units")
        except tk.TclError:
            pass

    def _bind_mousewheel(self, widget):
        """Bind mouse wheel scrolling to the provided widget."""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    def _update_scrollbar_visibility(self):
        """Show or hide the vertical scrollbar based on content height."""
        if not hasattr(self, 'vertical_scrollbar'):
            return

        try:
            required_height = self.main_frame.winfo_reqheight()
            canvas_height = self.scroll_canvas.winfo_height()
        except tk.TclError:
            return

        should_show = required_height > canvas_height + 1

        if should_show and not self._scrollbar_visible:
            self.vertical_scrollbar.pack(side="right", fill="y")
            self.scroll_canvas.configure(yscrollcommand=self.vertical_scrollbar.set)
            self._scrollbar_visible = True
        elif not should_show and self._scrollbar_visible:
            self.vertical_scrollbar.pack_forget()
            self.scroll_canvas.configure(yscrollcommand=None)
            self.scroll_canvas.yview_moveto(0)
            self._scrollbar_visible = False
    
    def _start_day(self):
        """Handle Start Day button click."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.START_DAY):
                if messagebox.askyesno("Confirm", "Start work day?"):
                    if self.worklog_manager.start_day():
                        self._update_display()
                        self._update_system_tray_status()
                        self.logger.info("Work day started")
                        self._notify_tray("Work Started", "Your work day has begun!")
                    else:
                        messagebox.showerror("Error", "Failed to start work day")
            else:
                messagebox.showwarning("Warning", "Cannot start day in current state")
        except Exception as e:
            self.logger.error(f"Error starting day: {e}")
            messagebox.showerror("Error", f"Failed to start day: {e}")
    
    def _end_day(self):
        """Handle End Day button click."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.END_DAY):
                # Get current calculations for confirmation
                calculations = self.worklog_manager.get_current_calculations()
                
                message = f"End work day?\n\n"
                message += (
                    "Productive time: "
                    f"{self.worklog_manager.time_calculator.format_duration_with_seconds(calculations.productive_seconds)}\n"
                )

                if calculations.is_overtime:
                    message += (
                        "Overtime: "
                        f"{self.worklog_manager.time_calculator.format_duration_with_seconds(calculations.overtime_seconds)}"
                    )
                else:
                    message += (
                        "Remaining: "
                        f"{self.worklog_manager.time_calculator.format_duration_with_seconds(calculations.remaining_seconds)}"
                    )
                
                if messagebox.askyesno("Confirm", message):
                    if self.worklog_manager.end_day():
                        self._update_display()
                        self._update_system_tray_status()
                        messagebox.showinfo("Day Complete", "Work day has been ended and saved.")
                        self.logger.info("Work day ended")
                        hours = calculations.productive_seconds // 3600
                        minutes = (calculations.productive_seconds % 3600) // 60
                        self._notify_tray("Work Day Ended", f"Productive time: {hours}h {minutes}m")
                    else:
                        messagebox.showerror("Error", "Failed to end work day")
            else:
                messagebox.showwarning("Warning", "Cannot end day in current state")
        except Exception as e:
            self.logger.error(f"Error ending day: {e}")
            messagebox.showerror("Error", f"Failed to end day: {e}")
    
    def _stop_work(self):
        """Handle Take a Break button click."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.STOP):
                break_type = BreakType(self.break_type_var.get())
                
                if messagebox.askyesno("Confirm", f"Start a {break_type.value.lower()} break?"):
                    if self.worklog_manager.stop_work(break_type):
                        self._update_display()
                        self._update_system_tray_status()
                        self.logger.info(f"Work paused for {break_type.value} break")
                        self._notify_tray("Break Started", f"Enjoy your {break_type.value.lower()} break!")
                    else:
                        messagebox.showerror("Error", "Failed to start break")
            else:
                messagebox.showwarning("Warning", "Cannot start a break in the current state")
        except Exception as e:
            self.logger.error(f"Error starting break: {e}")
            messagebox.showerror("Error", f"Failed to start break: {e}")
    
    def _continue_work(self):
        """Handle Resume Work button click."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.CONTINUE):
                if messagebox.askyesno("Confirm", "Resume working?"):
                    if self.worklog_manager.continue_work():
                        self._update_display()
                        self._update_system_tray_status()
                        self.logger.info("Work resumed")
                        self._notify_tray("Work Resumed", "Back to work!")
                    else:
                        messagebox.showerror("Error", "Failed to resume work")
            else:
                messagebox.showwarning("Warning", "Cannot resume work in the current state")
        except Exception as e:
            self.logger.error(f"Error resuming work: {e}")
            messagebox.showerror("Error", f"Failed to resume work: {e}")

    def _notify_tray(self, title: str, message: str):
        """Send a notification via the system tray if available."""
        if not self.system_tray_manager:
            return

        try:
            self.system_tray_manager.show_notification(title, message)
        except Exception as exc:
            self.logger.debug(f"Tray notification failed: {exc}")

    # Tray action wrappers - invoked via system tray callbacks without dialogs
    def start_work_from_tray(self):
        """Start work day without confirmation (tray action)."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.START_DAY):
                if self.worklog_manager.start_day():
                    self._update_display()
                    self._update_system_tray_status()
                    self.logger.info("Work day started from tray")
                    self._notify_tray("Work Started", "Your work day has begun!")
                else:
                    self.logger.error("Failed to start work day from tray")
                    self._notify_tray("Error", "Failed to start work day")
        except Exception as e:
            self.logger.error(f"Error starting day from tray: {e}")

    def end_work_from_tray(self):
        """End work day without confirmation (tray action)."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.END_DAY):
                if self.worklog_manager.end_day():
                    self._update_display()
                    self._update_system_tray_status()
                    self.logger.info("Work day ended from tray")
                    calculations = self.worklog_manager.get_current_calculations()
                    hours = calculations.productive_seconds // 3600
                    minutes = (calculations.productive_seconds % 3600) // 60
                    self._notify_tray("Work Day Ended", f"Productive time: {hours}h {minutes}m")
                else:
                    self.logger.error("Failed to end work day from tray")
                    self._notify_tray("Error", "Failed to end work day")
        except Exception as e:
            self.logger.error(f"Error ending day from tray: {e}")

    def take_break_from_tray(self):
        """Start a break without dialog (tray action)."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.STOP):
                break_type = BreakType(self.break_type_var.get())
                if self.worklog_manager.stop_work(break_type):
                    self._update_display()
                    self._update_system_tray_status()
                    self.logger.info(f"Break started from tray: {break_type.value}")
                    self._notify_tray("Break Started", f"Enjoy your {break_type.value.lower()} break!")
                else:
                    self.logger.error("Failed to start break from tray")
                    self._notify_tray("Error", "Failed to start break")
        except Exception as e:
            self.logger.error(f"Error starting break from tray: {e}")

    def resume_work_from_tray(self):
        """Resume work without dialog (tray action)."""
        try:
            if self.worklog_manager.can_perform_action(ActionType.CONTINUE):
                if self.worklog_manager.continue_work():
                    self._update_display()
                    self._update_system_tray_status()
                    self.logger.info("Work resumed from tray")
                    self._notify_tray("Work Resumed", "Back to work!")
                else:
                    self.logger.error("Failed to resume work from tray")
                    self._notify_tray("Error", "Failed to resume work")
        except Exception as e:
            self.logger.error(f"Error resuming work from tray: {e}")

    def get_tray_is_working(self):
        """Return True when a work session is in progress for tray monitoring."""
        try:
            state = self.worklog_manager.get_current_state()
            return state in (WorklogState.WORKING, WorklogState.ON_BREAK)
        except Exception:
            return False

    def get_tray_is_on_break(self):
        """Return True when the current state indicates an active break."""
        try:
            return self.worklog_manager.get_current_state() == WorklogState.ON_BREAK
        except Exception:
            return False

    def get_tray_work_start_time(self):
        """Return the workday start time as a datetime for tray displays."""
        session = getattr(self.worklog_manager, "current_session", None)
        if not session or not session.start_time:
            return None

        try:
            return self.worklog_manager.time_calculator.parse_time(session.start_time)
        except Exception:
            try:
                return datetime.fromisoformat(session.start_time)
            except Exception:
                return None

    def _update_system_tray_status(self):
        """Update system tray icon based on the current worklog state."""
        if not self.system_tray_manager:
            return

        try:
            state = self.worklog_manager.get_current_state()
            work_start_time = None
            is_on_break = False

            if state == WorklogState.NOT_STARTED:
                tray_status = "idle"
            elif state == WorklogState.WORKING:
                tray_status = "working"
                work_start_time = self.get_tray_work_start_time()
            elif state == WorklogState.ON_BREAK:
                tray_status = "break"
                is_on_break = True
                work_start_time = self.get_tray_work_start_time()
            elif state == WorklogState.DAY_ENDED:
                tray_status = "idle"
            else:
                tray_status = "idle"

            self.system_tray_manager.update_status(tray_status, work_start_time, is_on_break)

        except Exception as e:
            self.logger.error(f"Error updating system tray status: {e}")
    
    def _export_data(self):
        """Handle Export Data button click."""
        try:
            from core.export_manager import ExportManager
            from core.export_models import ExportFormat, ReportType, DateRange
            from datetime import date, timedelta
            import tkinter.filedialog as filedialog
            
            export_manager = ExportManager(self.worklog_manager.db)
            
            # Create custom dialog for export options
            export_dialog = tk.Toplevel(self.root)
            export_dialog.title("Export Data")
            export_dialog.geometry("450x400")
            export_dialog.transient(self.root)
            export_dialog.grab_set()
            
            # Center the dialog
            export_dialog.update_idletasks()
            x = (export_dialog.winfo_screenwidth() // 2) - (export_dialog.winfo_width() // 2)
            y = (export_dialog.winfo_screenheight() // 2) - (export_dialog.winfo_height() // 2)
            export_dialog.geometry(f"+{x}+{y}")
            
            # Main content frame with scrollbar
            main_frame = ttk.Frame(export_dialog)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Add title
            ttk.Label(main_frame, text="Select Export Options:", font=self._get_font_config(size_modifier=2, bold=True)).pack(pady=(0, 10))
            
            # Date range selection
            range_frame = ttk.LabelFrame(main_frame, text="Date Range", padding=10)
            range_frame.pack(fill='x', pady=5)
            
            date_range_var = tk.StringVar(value="today")
            ttk.Radiobutton(range_frame, text="Today Only", variable=date_range_var, value="today").pack(anchor='w', pady=2)
            ttk.Radiobutton(range_frame, text="This Week", variable=date_range_var, value="week").pack(anchor='w', pady=2)
            ttk.Radiobutton(range_frame, text="Custom Date Range...", variable=date_range_var, value="custom").pack(anchor='w', pady=2)
            
            # Format selection (checkboxes)
            format_frame = ttk.LabelFrame(main_frame, text="Export Formats (select one or more)", padding=10)
            format_frame.pack(fill='x', pady=5)
            
            csv_var = tk.BooleanVar(value=True)
            json_var = tk.BooleanVar(value=False)
            pdf_var = tk.BooleanVar(value=False)
            
            ttk.Checkbutton(format_frame, text="CSV Format", variable=csv_var).pack(anchor='w', pady=2)
            ttk.Checkbutton(format_frame, text="JSON Format", variable=json_var).pack(anchor='w', pady=2)
            ttk.Checkbutton(format_frame, text="PDF Format", variable=pdf_var).pack(anchor='w', pady=2)
            
            # Button frame at bottom
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=20, fill='x')
            
            result = {'exports': []}
            
            def on_export():
                selected_formats = []
                if csv_var.get():
                    selected_formats.append(ExportFormat.CSV)
                if json_var.get():
                    selected_formats.append(ExportFormat.JSON)
                if pdf_var.get():
                    selected_formats.append(ExportFormat.PDF)
                
                if not selected_formats:
                    messagebox.showwarning("No Format Selected", "Please select at least one export format.", parent=export_dialog)
                    return
                
                result['exports'] = [(date_range_var.get(), fmt) for fmt in selected_formats]
                export_dialog.destroy()
            
            def on_cancel():
                export_dialog.destroy()
            
            # Center buttons
            btn_container = ttk.Frame(btn_frame)
            btn_container.pack(expand=True)
            ttk.Button(btn_container, text="Export", command=on_export, width=15).pack(side='left', padx=5)
            ttk.Button(btn_container, text="Cancel", command=on_cancel, width=15).pack(side='left', padx=5)
            
            # Wait for dialog to close
            self.root.wait_window(export_dialog)
            
            if not result['exports']:
                return  # User cancelled
            
            # Process all selected exports
            export_results = []
            for date_range, export_format in result['exports']:
                if date_range == "today":
                    export_result = export_manager.export_today(export_format)
                    export_results.append(export_result)
                elif date_range == "week":
                    export_result = export_manager.export_week(export_format)
                    export_results.append(export_result)
                elif date_range == "custom":
                    # Show file save dialog for custom date range
                    # Export last 7 days by default for custom
                    end_date = date.today()
                    start_date = end_date - timedelta(days=6)
                    
                    export_result = export_manager.export_date_range(
                        export_format,
                        start_date,
                        end_date,
                        ReportType.DAILY_SUMMARY
                    )
                    export_results.append(export_result)
            
            # Show results
            successful_exports = [r for r in export_results if r.success]
            failed_exports = [r for r in export_results if not r.success]
            
            if successful_exports:
                files_list = "\n".join([
                    f"• {os.path.basename(r.filepath)}" for r in successful_exports
                ])
                
                messagebox.showinfo(
                    "Export Successful", 
                    f"Successfully exported {len(successful_exports)} file(s):\n\n{files_list}\n\n"
                    f"Location: {os.path.dirname(successful_exports[0].filepath)}"
                )
                
                # Ask if user wants to open the folder
                if messagebox.askyesno("Open Folder", "Would you like to open the exports folder?"):
                    import subprocess
                    folder = os.path.dirname(successful_exports[0].filepath)
                    if os.name == 'nt':  # Windows
                        os.startfile(folder)
                    else:  # Linux/Mac
                        subprocess.Popen(['xdg-open', folder])
            
            if failed_exports:
                errors_list = "\n".join([
                    f"• {r.error_message}" for r in failed_exports
                ])
                messagebox.showerror(
                    "Export Errors",
                    f"{len(failed_exports)} export(s) failed:\n\n{errors_list}"
                )
                
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def _revoke_action(self):
        """Handle Revoke Action button click."""
        try:
            action_history = self.worklog_manager.get_action_history()
            
            # Check if there are any revokable actions
            revokable_actions = action_history.get_revokable_actions()
            if not revokable_actions:
                messagebox.showinfo("No Actions", "There are no actions to revoke.")
                return
            
            # Show revoke dialog
            result = show_revoke_dialog(
                self.root, 
                action_history, 
                self._perform_revoke
            )
            
            if result:
                # Update display after successful revoke
                self._update_display()
                
        except Exception as e:
            self.logger.error(f"Error in revoke dialog: {e}")
            messagebox.showerror("Error", f"Failed to open revoke dialog: {e}")
    
    def _perform_revoke(self, action_id: str) -> bool:
        """Perform the actual revoke operation.
        
        Args:
            action_id: ID of the action to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.worklog_manager.revoke_action(action_id)
        except Exception as e:
            self.logger.error(f"Error revoking action {action_id}: {e}")
            return False
    
    def _reset_day(self):
        """Handle Reset Day button click."""
        try:
            # Show confirmation dialog with warning
            result = messagebox.askyesno(
                "Reset Day - Warning!",
                "This will completely delete all data for today including:\n"
                "• All work sessions\n"
                "• All break periods\n"
                "• All action history\n"
                "• Timer progress\n\n"
                "This action CANNOT be undone!\n\n"
                "Are you sure you want to reset today?",
                icon='warning'
            )
            
            if result:
                # Second confirmation for safety
                final_confirm = messagebox.askyesno(
                    "Final Confirmation",
                    "Last chance! Reset the entire day?\n\n"
                    "ALL TODAY'S DATA WILL BE PERMANENTLY DELETED!",
                    icon='warning'
                )
                
                if final_confirm:
                    success = self.worklog_manager.reset_day()
                    
                    if success:
                        messagebox.showinfo("Success", "Day has been reset successfully!")
                        self._update_display()
                    else:
                        messagebox.showerror("Error", "Failed to reset day. Check logs for details.")
                        
        except Exception as e:
            self.logger.error(f"Error resetting day: {e}")
            messagebox.showerror("Error", f"Failed to reset day: {e}")

    def _show_settings(self):
        """Handle Settings button click - Open comprehensive settings dialog."""
        try:
            from gui.settings_dialog import SettingsDialog
            
            # Create and show settings dialog
            def on_settings_changed(settings=None):
                """Callback when settings are changed."""
                try:
                    # Only reload if settings not provided (settings already saved by dialog)
                    if settings is None:
                        self.settings_manager.load_settings()
                        settings = self.settings_manager.settings
                    
                    # Update worklog manager with new settings if it has a settings reference
                    if hasattr(self.worklog_manager, 'settings_manager'):
                        self.worklog_manager.settings_manager = self.settings_manager
                    
                    # Update timer display and break tracker with new settings
                    # Note: update_settings_manager already calls _update_fonts internally
                    if hasattr(self.timer_display, 'update_settings_manager'):
                        self.timer_display.update_settings_manager(self.settings_manager)
                    if hasattr(self.break_tracker, 'settings_manager'):
                        self.break_tracker.settings_manager = self.settings_manager
                    
                    # Update fonts in main window UI (not timer_display, already done above)
                    if hasattr(self, 'date_label') and self.date_label:
                        self.date_label.config(font=self._get_font_config(size_modifier=2, bold=True))
                    if hasattr(self, 'status_label') and self.status_label:
                        self.status_label.config(font=self._get_font_config(size_modifier=2, bold=True))
                    
                    # Apply fonts globally through theme manager
                    if self.theme_manager and hasattr(settings, 'appearance'):
                        font_family = settings.appearance.font_family
                        font_size = settings.appearance.font_size
                        self.logger.info(f"Applying fonts globally: {font_family} {font_size}pt")
                        self.theme_manager.apply_fonts(font_family, font_size)
                    
                    self.logger.info("Settings updated successfully")
                        
                    # Note: _update_display() is not called here as it's expensive and the
                    # worklog state hasn't changed. It will be called on the next timer update.
                    
                    # Apply theme changes ONLY if theme has actually changed
                    if self.theme_manager:
                        try:
                            if hasattr(settings, 'appearance'):
                                theme_value = settings.appearance.theme
                                if hasattr(theme_value, 'value'):
                                    theme_value = theme_value.value
                                # Only apply if theme changed
                                if theme_value != self.theme_manager.current_theme:
                                    self.logger.info(f"Theme changed from {self.theme_manager.current_theme} to {theme_value}, applying...")
                                    self.theme_manager.apply_theme(theme_value)
                                else:
                                    self.logger.debug(f"Theme unchanged ({theme_value}), skipping theme application")
                        except Exception as e:
                            self.logger.error(f"Error applying theme: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error in on_settings_changed: {e}")
            
            settings_dialog = SettingsDialog(
                parent=self.root,
                settings_manager=self.settings_manager,
                theme_manager=self.theme_manager,
                backup_manager=self.backup_manager,
                on_settings_changed=on_settings_changed
            )
            
        except ImportError as e:
            self.logger.error(f"Settings dialog not available: {e}")
            messagebox.showwarning("Settings Unavailable", 
                                 "Settings dialog is not available. "
                                 "Some Phase 4 components may not be installed properly.")
        except Exception as e:
            self.logger.error(f"Error opening settings: {e}")
            messagebox.showerror("Error", f"Could not open settings dialog: {e}")
    
    def _update_fonts(self):
        """Update fonts in all UI components based on current settings."""
        try:
            # Update date label
            if hasattr(self, 'date_label') and self.date_label:
                self.date_label.config(font=self._get_font_config(size_modifier=2, bold=True))
            
            # Update status label
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.config(font=self._get_font_config(size_modifier=2, bold=True))
            
            # Update timer display fonts
            if hasattr(self, 'timer_display') and self.timer_display:
                if hasattr(self.timer_display, '_update_fonts'):
                    self.timer_display._update_fonts()
            
            self.logger.info("Updated fonts based on settings")
        except Exception as e:
            self.logger.error(f"Error updating fonts: {e}")
    
    def _update_display(self):
        """Update the display with current state and calculations."""
        try:
            # Update status
            state = self.worklog_manager.get_current_state()
            status_text = {
                WorklogState.NOT_STARTED: "Status: Not Started",
                WorklogState.WORKING: "Status: Working",
                WorklogState.ON_BREAK: "Status: On Break",
                WorklogState.DAY_ENDED: "Status: Day Ended"
            }
            self.status_var.set(status_text.get(state, "Status: Unknown"))
            
            # Update status color
            status_colors = {
                WorklogState.NOT_STARTED: "#666666",
                WorklogState.WORKING: "#006400",
                WorklogState.ON_BREAK: "#FF8C00",
                WorklogState.DAY_ENDED: "#DC143C"
            }
            
            # Find the status label and update its color
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, tk.Label) and grandchild.cget("textvariable") == str(self.status_var):
                                    grandchild.config(fg=status_colors.get(state, "#000000"))
            
            # Update button states
            self.start_day_btn.config(state="normal" if self.worklog_manager.can_perform_action(ActionType.START_DAY) else "disabled")
            self.end_day_btn.config(state="normal" if self.worklog_manager.can_perform_action(ActionType.END_DAY) else "disabled")
            self.stop_btn.config(state="normal" if self.worklog_manager.can_perform_action(ActionType.STOP) else "disabled")
            self.continue_btn.config(state="normal" if self.worklog_manager.can_perform_action(ActionType.CONTINUE) else "disabled")
            
            # Update timer display
            calculations = self.worklog_manager.get_current_calculations()
            current_session_seconds = 0
            
            if state == WorklogState.WORKING:
                # Get current session time in seconds
                actions = self.worklog_manager.db.get_session_actions(self.worklog_manager.current_session.id)
                current_session_seconds = self.worklog_manager.time_calculator.calculate_current_session_time(actions)
            
            self.timer_display.update_display(calculations, current_session_seconds)
            
            # Update break tracker
            if self.worklog_manager.current_session:
                breaks = self.worklog_manager.db.get_session_breaks(self.worklog_manager.current_session.id)
                self.break_tracker.update_breaks(breaks)
            
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
    
    def _timer_update(self):
        """Called by timer thread for real-time updates."""
        try:
            # Schedule GUI update on main thread
            self.root.after(0, self._update_display)
        except Exception as e:
            self.logger.error(f"Timer update error: {e}")
    
    def _on_closing(self):
        """Handle window closing event."""
        try:
            # Check if we should minimize to tray instead of closing
            general_settings = self.settings_manager.settings.general
            
            # If system tray is enabled and minimize_to_tray is enabled, just hide the window
            if general_settings.system_tray_enabled and general_settings.minimize_to_tray:
                self.root.withdraw()  # Hide the window instead of closing
                return
            
            # Otherwise, proceed with normal exit confirmation and cleanup
            if general_settings.confirm_exit:
                if not messagebox.askyesno("Confirm Exit", "Are you sure you want to exit the application?"):
                    return  # User cancelled, don't close
            
            # Perform actual exit
            self._perform_exit()
            
        except Exception as e:
            self.logger.error(f"Error during closing: {e}")
    
    def _perform_exit(self):
        """Perform the actual exit operations (save settings and close)."""
        try:
            # Save window geometry if remember settings are enabled
            appearance_settings = self.settings_manager.settings.appearance
            
            # Check if window is maximized
            is_maximized = self.root.state() == 'zoomed'
            
            # Only save position and size if window is NOT maximized
            # Do NOT save the maximized state - that should only be set via Settings dialog
            if appearance_settings.remember_window_position and not is_maximized:
                # Get current window geometry
                geometry = self.root.geometry()
                # Parse geometry string: "widthxheight+x+y"
                size_pos = geometry.split('+')
                if len(size_pos) >= 3:
                    width_height = size_pos[0].split('x')
                    appearance_settings.window_width = int(width_height[0])
                    appearance_settings.window_height = int(width_height[1])
                    appearance_settings.window_x = int(size_pos[1])
                    appearance_settings.window_y = int(size_pos[2])
                    # Save settings
                    self.settings_manager.save_settings()
            elif not is_maximized:
                # Just save size if only size should be remembered
                geometry = self.root.geometry()
                size_pos = geometry.split('+')
                if len(size_pos) >= 1:
                    width_height = size_pos[0].split('x')
                    appearance_settings.window_width = int(width_height[0])
                    appearance_settings.window_height = int(width_height[1])
                    # Save settings
                    self.settings_manager.save_settings()
            
            # Stop timer
            self.worklog_manager.stop_timer()
            
            # Close the window
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during closing: {e}")
    
    def show_window(self):
        """Show the main window (used by system tray)."""
        self.root.deiconify()
        if self._was_maximized:
            self.root.state('zoomed')
        else:
            self.root.state('normal')
            if self._saved_geometry:
                try:
                    self.root.geometry(self._saved_geometry)
                except tk.TclError as exc:
                    self.logger.debug(f"Failed to restore geometry {self._saved_geometry}: {exc}")
        self.root.lift()
        self.root.focus_force()
        
        # Reapply theme to ensure correct colors after window restore
        if self.theme_manager:
            try:
                current_theme = self.settings_manager.settings.appearance.theme
                if hasattr(current_theme, 'value'):
                    current_theme = current_theme.value
                self.logger.debug(f"Reapplying theme '{current_theme}' after window restore")
                self.theme_manager.apply_theme(current_theme)
                self.root.update_idletasks()
            except Exception as e:
                self.logger.error(f"Error reapplying theme on window restore: {e}")
    
    def hide_window(self):
        """Hide the main window to system tray."""
        current_state = self.root.state()
        if current_state == 'zoomed':
            self._was_maximized = True
        else:
            self._was_maximized = False
            try:
                self._saved_geometry = self.root.geometry()
            except tk.TclError:
                pass
        
        # Mark that window is being hidden
        self._window_was_hidden = True
        
        self.root.withdraw()

    def toggle_window_visibility(self):
        """Toggle visibility while preserving geometry and maximize state."""
        current_state = self.root.state()
        if current_state in ('withdrawn', 'iconic'):
            self.logger.debug("Restoring window from system tray toggle")
            self.show_window()
        else:
            self.logger.debug("Hiding window via system tray toggle")
            self.hide_window()

    def _on_window_configure(self, event):
        """Track window maximize/normalize state changes."""
        try:
            current_state = self.root.state()
            if current_state in ('zoomed', 'normal'):
                self._was_maximized = current_state == 'zoomed'
                if current_state == 'normal' and self.root.winfo_viewable():
                    self._saved_geometry = self.root.geometry()
        except tk.TclError as exc:
            self.logger.debug(f"Configure state tracking failed: {exc}")
    
    def quit_application(self):
        """Quit the application completely (called by system tray)."""
        general_settings = self.settings_manager.settings.general
        if general_settings.confirm_exit:
            if not messagebox.askyesno("Confirm Exit", "Are you sure you want to exit the application?"):
                return False  # User cancelled
        
        self._perform_exit()
        return True

    def open_settings_from_tray(self):
        """Restore the window and open settings when invoked from system tray."""
        try:
            self.show_window()
            self._show_settings()
        except Exception as exc:
            self.logger.error(f"Failed to open settings from tray: {exc}")
    
    def run(self):
        """Start the application main loop."""
        try:
            self.logger.info("Starting Worklog Manager application")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Application Error", f"An unexpected error occurred: {e}")
        finally:
            # Ensure cleanup
            self.worklog_manager.stop_timer()