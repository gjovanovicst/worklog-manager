"""Enhanced break management component."""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any
import logging

from data.models import BreakType, BreakPeriod
from core.time_calculator import TimeCalculator


class BreakTracker(ttk.Frame):
    """Component for tracking and displaying break information."""
    
    def __init__(self, parent):
        """Initialize the break tracker.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.time_calculator = TimeCalculator()
        
        # Store references to themed widgets
        self.lunch_frame = None
        self.lunch_labels = []
        self.coffee_frame = None
        self.coffee_labels = []
        self.general_frame = None
        self.general_labels = []
        self.breaks_listbox = None
        self.header_labels = []
        
        self._create_widgets()
        self._break_periods: List[BreakPeriod] = []
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main frame
        main_frame = ttk.LabelFrame(self, text="Break Summary", padding="5")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Break summary grid
        self._create_summary_grid(main_frame)
        
        # Recent breaks list
        self._create_recent_breaks(main_frame)
    
    def _create_summary_grid(self, parent):
        """Create break summary grid.
        
        Args:
            parent: Parent widget
        """
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill="x", pady=(0, 10))
        
        # Headers
        header1 = tk.Label(summary_frame, text="Break Type", font=("Arial", 9, "bold"))
        header1.grid(row=0, column=0, sticky="w", padx=(0, 20))
        header2 = tk.Label(summary_frame, text="Count", font=("Arial", 9, "bold"))
        header2.grid(row=0, column=1, sticky="w", padx=(0, 20))
        header3 = tk.Label(summary_frame, text="Total Time", font=("Arial", 9, "bold"))
        header3.grid(row=0, column=2, sticky="w")
        self.header_labels = [header1, header2, header3]
        
        # Break type rows
        zero_time = self.time_calculator.format_duration_with_seconds(0)
        self.lunch_count_var = tk.StringVar(value="0")
        self.lunch_time_var = tk.StringVar(value=zero_time)
        self.coffee_count_var = tk.StringVar(value="0")
        self.coffee_time_var = tk.StringVar(value=zero_time)
        self.general_count_var = tk.StringVar(value="0")
        self.general_time_var = tk.StringVar(value=zero_time)
        
        # Lunch breaks
        self.lunch_frame = tk.Frame(summary_frame, relief="ridge", bd=1)
        self.lunch_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=1)
        self.lunch_frame.columnconfigure(2, weight=1)
        
        lunch_label1 = tk.Label(self.lunch_frame, text="[L] Lunch")
        lunch_label1.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        lunch_label2 = tk.Label(self.lunch_frame, textvariable=self.lunch_count_var)
        lunch_label2.grid(row=0, column=1, padx=20, pady=2)
        lunch_label3 = tk.Label(self.lunch_frame, textvariable=self.lunch_time_var)
        lunch_label3.grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.lunch_labels = [lunch_label1, lunch_label2, lunch_label3]
        
        # Coffee breaks
        self.coffee_frame = tk.Frame(summary_frame, relief="ridge", bd=1)
        self.coffee_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=1)
        self.coffee_frame.columnconfigure(2, weight=1)
        
        coffee_label1 = tk.Label(self.coffee_frame, text="[C] Coffee")
        coffee_label1.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        coffee_label2 = tk.Label(self.coffee_frame, textvariable=self.coffee_count_var)
        coffee_label2.grid(row=0, column=1, padx=20, pady=2)
        coffee_label3 = tk.Label(self.coffee_frame, textvariable=self.coffee_time_var)
        coffee_label3.grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.coffee_labels = [coffee_label1, coffee_label2, coffee_label3]
        
        # General breaks
        self.general_frame = tk.Frame(summary_frame, relief="ridge", bd=1)
        self.general_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=1)
        self.general_frame.columnconfigure(2, weight=1)
        
        general_label1 = tk.Label(self.general_frame, text="[B] General")
        general_label1.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        general_label2 = tk.Label(self.general_frame, textvariable=self.general_count_var)
        general_label2.grid(row=0, column=1, padx=20, pady=2)
        general_label3 = tk.Label(self.general_frame, textvariable=self.general_time_var)
        general_label3.grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.general_labels = [general_label1, general_label2, general_label3]
        
        summary_frame.columnconfigure(0, weight=1)
    
    def _create_recent_breaks(self, parent):
        """Create recent breaks list.
        
        Args:
            parent: Parent widget
        """
        recent_frame = ttk.LabelFrame(parent, text="Recent Breaks", padding="5")
        recent_frame.pack(fill="both", expand=True)
        
        # Create listbox with scrollbar
        listbox_frame = ttk.Frame(recent_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.breaks_listbox = tk.Listbox(listbox_frame, height=4, font=("Arial", 8))
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.breaks_listbox.yview)
        self.breaks_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.breaks_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def update_breaks(self, break_periods: List[BreakPeriod]):
        """Update break display with new data.
        
        Args:
            break_periods: List of BreakPeriod objects
        """
        self._break_periods = break_periods
        self._update_summary()
        self._update_recent_list()
    
    def _update_summary(self):
        """Update the break summary counts and times."""
        # Count breaks by type
        lunch_breaks = [b for b in self._break_periods if b.break_type == BreakType.LUNCH]
        coffee_breaks = [b for b in self._break_periods if b.break_type == BreakType.COFFEE]
        general_breaks = [b for b in self._break_periods if b.break_type == BreakType.GENERAL]
        
        # Calculate total times (seconds precision)
        lunch_time = sum(self._break_duration_seconds(b) for b in lunch_breaks)
        coffee_time = sum(self._break_duration_seconds(b) for b in coffee_breaks)
        general_time = sum(self._break_duration_seconds(b) for b in general_breaks)
        
        # Update variables
        self.lunch_count_var.set(str(len(lunch_breaks)))
        self.lunch_time_var.set(self._format_seconds(lunch_time))
        
        self.coffee_count_var.set(str(len(coffee_breaks)))
        self.coffee_time_var.set(self._format_seconds(coffee_time))
        
        self.general_count_var.set(str(len(general_breaks)))
        self.general_time_var.set(self._format_seconds(general_time))
    
    def _update_recent_list(self):
        """Update the recent breaks list."""
        self.breaks_listbox.delete(0, tk.END)
        
        if not self._break_periods:
            self.breaks_listbox.insert(tk.END, "No breaks taken today")
            return
        
        # Show most recent breaks first
        recent_breaks = sorted(self._break_periods, 
                             key=lambda x: x.start_time, reverse=True)[:10]
        
        for break_period in recent_breaks:
            start_time = self._format_timestamp(break_period.start_time)
            
            if break_period.end_time:
                end_time = self._format_timestamp(break_period.end_time)
                duration = self._format_seconds(self._break_duration_seconds(break_period))
                status = f"{start_time}-{end_time} ({duration})"
            else:
                status = f"{start_time}-ongoing"
            
            # Add ASCII symbol based on break type for broad interpreter support
            symbol = {
                BreakType.LUNCH: "[L]",
                BreakType.COFFEE: "[C]",
                BreakType.GENERAL: "[B]"
            }.get(break_period.break_type, "[B]")
            
            break_text = f"{symbol} {break_period.break_type.value.title()}: {status}"
            self.breaks_listbox.insert(tk.END, break_text)
    
    def _break_duration_seconds(self, break_period: BreakPeriod) -> int:
        """Calculate break duration in seconds."""
        try:
            if break_period.start_time and break_period.end_time:
                start = self.time_calculator.parse_time(break_period.start_time)
                end = self.time_calculator.parse_time(break_period.end_time)
                return max(0, int((end - start).total_seconds()))
            if break_period.duration_minutes is not None:
                return max(0, int(break_period.duration_minutes * 60))
        except Exception as error:
            self.logger.debug(f"Failed to calculate break duration: {error}")
        return 0

    def _format_seconds(self, total_seconds: int) -> str:
        """Format seconds to HH:MM:SS string."""
        if total_seconds <= 0:
            return self.time_calculator.format_duration_with_seconds(0)
        return self.time_calculator.format_duration_with_seconds(total_seconds)

    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to HH:MM:SS."""
        if not timestamp:
            return "--:--:--"
        try:
            dt_value = self.time_calculator.parse_time(timestamp)
            return dt_value.strftime("%H:%M:%S")
        except Exception:
            if 'T' in timestamp and len(timestamp.split('T')[1]) >= 8:
                return timestamp.split('T')[1][:8]
            return timestamp[:8] if len(timestamp) >= 8 else timestamp
    
    def get_break_summary(self) -> Dict[str, Any]:
        """Get summary of break data.
        
        Returns:
            Dictionary with break summary information
        """
        lunch_breaks = [b for b in self._break_periods if b.break_type == BreakType.LUNCH]
        coffee_breaks = [b for b in self._break_periods if b.break_type == BreakType.COFFEE]
        general_breaks = [b for b in self._break_periods if b.break_type == BreakType.GENERAL]
        
        return {
            'total_breaks': len(self._break_periods),
            'lunch': {
                'count': len(lunch_breaks),
                'time': sum(b.duration_minutes or 0 for b in lunch_breaks)
            },
            'coffee': {
                'count': len(coffee_breaks),
                'time': sum(b.duration_minutes or 0 for b in coffee_breaks)
            },
            'general': {
                'count': len(general_breaks),
                'time': sum(b.duration_minutes or 0 for b in general_breaks)
            },
            'total_time': sum(b.duration_minutes or 0 for b in self._break_periods)
        }
    
    def register_with_theme_manager(self, theme_manager):
        """Register widgets with the theme manager for theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        if theme_manager:
            self.logger.debug("Registering BreakTracker widgets with theme manager")
            # Register header labels
            for header in self.header_labels:
                theme_manager.register_widget(header, 'label')
            
            # Register break frames with subtle backgrounds
            if self.lunch_frame:
                theme_manager.register_widget(self.lunch_frame, 'break_lunch_bg')
            if self.coffee_frame:
                theme_manager.register_widget(self.coffee_frame, 'break_coffee_bg')
            if self.general_frame:
                theme_manager.register_widget(self.general_frame, 'break_general_bg')
            
            # Register labels for each break type
            for label in self.lunch_labels:
                theme_manager.register_widget(label, 'break_lunch_label')
            for label in self.coffee_labels:
                theme_manager.register_widget(label, 'break_coffee_label')
            for label in self.general_labels:
                theme_manager.register_widget(label, 'break_general_label')
            
            # Register listbox
            if self.breaks_listbox:
                theme_manager.register_widget(self.breaks_listbox, 'listbox')
            
            self.logger.debug("BreakTracker widgets registered successfully")