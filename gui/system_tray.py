"""
System Tray Integration for Worklog Manager Application

Provides system tray functionality for minimized operation, quick actions,
and background notifications. Supports cross-platform system tray integration.
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading
import base64
from typing import Optional, Callable, Dict, List
from datetime import datetime
import time

# Try to import pystray for system tray functionality
try:
    import pystray
    from pystray import MenuItem as Item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray not available. System tray functionality will be limited.")

# Try to import PIL for icon creation
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class SystemTrayManager:
    """Manages system tray integration for the worklog application."""
    
    def __init__(self, root: tk.Tk, app_name: str = "Worklog Manager"):
        self.root = root
        self.app_name = app_name
        self.tray_icon = None
        self.tray_thread = None
        self.running = False
        
        # Application callbacks
        self.callbacks: Dict[str, Callable] = {}
        
        # Tray state
        self.current_status = "idle"
        self.work_start_time = None
        self.is_on_break = False
        
        # Create default icon
        self.icon_image = self.create_default_icon()
        
        # Setup protocol for window close
        self.original_protocol = None
        self.setup_window_protocol()
    
    def create_default_icon(self):
        """Create a default icon for the system tray."""
        if PIL_AVAILABLE:
            # Create a simple colored icon
            size = (64, 64)
            image = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a clock-like icon
            center = (size[0] // 2, size[1] // 2)
            radius = size[0] // 2 - 4
            
            # Outer circle
            draw.ellipse([center[0] - radius, center[1] - radius,
                         center[0] + radius, center[1] + radius],
                        fill='#2c3e50', outline='#34495e', width=2)
            
            # Clock hands
            draw.line([center[0], center[1], center[0], center[1] - radius + 10],
                     fill='white', width=3)
            draw.line([center[0], center[1], center[0] + radius - 15, center[1]],
                     fill='white', width=2)
            
            # Center dot
            draw.ellipse([center[0] - 3, center[1] - 3,
                         center[0] + 3, center[1] + 3], fill='white')
            
            return image
        else:
            # Fallback: try to use a default system icon
            return None
    
    def create_status_icon(self, status: str):
        """Create an icon based on current work status."""
        if not PIL_AVAILABLE:
            return self.icon_image
        
        size = (64, 64)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        center = (size[0] // 2, size[1] // 2)
        radius = size[0] // 2 - 4
        
        # Choose color based on status
        if status == "working":
            color = '#27ae60'  # Green
        elif status == "break":
            color = '#f39c12'  # Orange
        elif status == "overtime":
            color = '#e74c3c'  # Red
        else:
            color = '#2c3e50'  # Dark blue-gray
        
        # Draw outer circle
        draw.ellipse([center[0] - radius, center[1] - radius,
                     center[0] + radius, center[1] + radius],
                    fill=color, outline='#34495e', width=2)
        
        # Draw status indicator
        if status == "working":
            # Play symbol (triangle)
            points = [
                (center[0] - 8, center[1] - 12),
                (center[0] - 8, center[1] + 12),
                (center[0] + 12, center[1])
            ]
            draw.polygon(points, fill='white')
        elif status == "break":
            # Pause symbol (two rectangles)
            draw.rectangle([center[0] - 8, center[1] - 10,
                           center[0] - 2, center[1] + 10], fill='white')
            draw.rectangle([center[0] + 2, center[1] - 10,
                           center[0] + 8, center[1] + 10], fill='white')
        elif status == "overtime":
            # Warning symbol (exclamation mark)
            draw.rectangle([center[0] - 2, center[1] - 12,
                           center[0] + 2, center[1] - 2], fill='white')
            draw.ellipse([center[0] - 2, center[1] + 2,
                         center[0] + 2, center[1] + 6], fill='white')
        else:
            # Clock hands for idle
            draw.line([center[0], center[1], center[0], center[1] - 10],
                     fill='white', width=3)
            draw.line([center[0], center[1], center[0] + 8, center[1]],
                     fill='white', width=2)
        
        return image
    
    def setup_window_protocol(self):
        """Setup window close protocol to minimize to tray instead of closing."""
        self.original_protocol = self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def on_window_close(self):
        """Handle window close event."""
        if self.tray_icon and self.running:
            # Minimize to tray
            self.hide_window()
        else:
            # Normal exit
            self.quit_application()
    
    def register_callback(self, action: str, callback: Callable):
        """Register a callback for tray menu actions."""
        self.callbacks[action] = callback
    
    def start_tray(self) -> bool:
        """Start the system tray."""
        if not PYSTRAY_AVAILABLE:
            print("System tray not available (pystray not installed)")
            return False
        
        if self.running:
            return True
        
        try:
            # Create tray menu
            menu = self.create_tray_menu()
            
            # Create tray icon
            icon_image = self.icon_image or self.create_status_icon("idle")
            self.tray_icon = pystray.Icon(
                self.app_name,
                icon_image,
                menu=menu,
                title=self.app_name
            )
            
            # Start tray in separate thread
            self.running = True
            self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            self.tray_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting system tray: {e}")
            return False
    
    def _run_tray(self):
        """Run the system tray (called in separate thread)."""
        try:
            if self.tray_icon:
                self.tray_icon.run()
        except Exception as e:
            print(f"Error running system tray: {e}")
        finally:
            self.running = False
    
    def stop_tray(self):
        """Stop the system tray."""
        self.running = False
        
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                print(f"Error stopping system tray: {e}")
        
        if self.tray_thread:
            self.tray_thread.join(timeout=2)
    
    def create_tray_menu(self):
        """Create the system tray menu."""
        if not PYSTRAY_AVAILABLE:
            return None
        
        return pystray.Menu(
            Item("Show Window", self.show_window),
            Item("Hide Window", self.hide_window),
            pystray.Menu.SEPARATOR,
            Item("Start Work", self.start_work_action, enabled=lambda item: self.current_status != "working"),
            Item("End Work", self.end_work_action, enabled=lambda item: self.current_status == "working"),
            pystray.Menu.SEPARATOR,
            Item("Take Break", self.take_break_action, enabled=lambda item: self.current_status == "working" and not self.is_on_break),
            Item("End Break", self.end_break_action, enabled=lambda item: self.is_on_break),
            pystray.Menu.SEPARATOR,
            Item("Daily Summary", self.show_summary_action),
            Item("Export Data", self.export_data_action),
            pystray.Menu.SEPARATOR,
            Item("Settings", self.show_settings_action),
            Item("About", self.show_about_action),
            pystray.Menu.SEPARATOR,
            Item("Quit", self.quit_application)
        )
    
    def update_status(self, status: str, work_start_time: datetime = None, is_on_break: bool = False):
        """Update the tray icon status."""
        self.current_status = status
        self.work_start_time = work_start_time
        self.is_on_break = is_on_break
        
        if self.tray_icon and self.running:
            try:
                # Update icon
                new_icon = self.create_status_icon(status)
                if new_icon:
                    self.tray_icon.icon = new_icon
                
                # Update tooltip
                tooltip = self.get_status_tooltip()
                self.tray_icon.title = tooltip
                
                # Update menu (recreate to refresh enabled states)
                self.tray_icon.menu = self.create_tray_menu()
                
            except Exception as e:
                print(f"Error updating tray status: {e}")
    
    def get_status_tooltip(self) -> str:
        """Get tooltip text based on current status."""
        tooltip = self.app_name
        
        if self.current_status == "working":
            if self.work_start_time:
                elapsed = datetime.now() - self.work_start_time
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                tooltip += f" - Working ({hours:02d}:{minutes:02d})"
            else:
                tooltip += " - Working"
            
            if self.is_on_break:
                tooltip += " (On Break)"
        
        elif self.current_status == "break":
            tooltip += " - On Break"
        elif self.current_status == "overtime":
            tooltip += " - Overtime!"
        else:
            tooltip += " - Idle"
        
        return tooltip
    
    def show_notification(self, title: str, message: str, timeout: int = 5):
        """Show a system notification through the tray icon."""
        if self.tray_icon and self.running:
            try:
                self.tray_icon.notify(message, title)
            except Exception as e:
                print(f"Error showing notification: {e}")
    
    # Menu action methods
    def show_window(self, item=None):
        """Show the main application window."""
        try:
            self.root.after(0, self._show_window_main_thread)
        except Exception as e:
            print(f"Error showing window: {e}")
    
    def _show_window_main_thread(self):
        """Show window in main thread."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self, item=None):
        """Hide the main application window."""
        try:
            self.root.after(0, self._hide_window_main_thread)
        except Exception as e:
            print(f"Error hiding window: {e}")
    
    def _hide_window_main_thread(self):
        """Hide window in main thread."""
        self.root.withdraw()
    
    def start_work_action(self, item=None):
        """Start work action from tray menu."""
        if "start_work" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["start_work"])
            except Exception as e:
                print(f"Error starting work: {e}")
    
    def end_work_action(self, item=None):
        """End work action from tray menu."""
        if "end_work" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["end_work"])
            except Exception as e:
                print(f"Error ending work: {e}")
    
    def take_break_action(self, item=None):
        """Take break action from tray menu."""
        if "take_break" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["take_break"])
            except Exception as e:
                print(f"Error taking break: {e}")
    
    def end_break_action(self, item=None):
        """End break action from tray menu."""
        if "end_break" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["end_break"])
            except Exception as e:
                print(f"Error ending break: {e}")
    
    def show_summary_action(self, item=None):
        """Show daily summary action from tray menu."""
        if "show_summary" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["show_summary"])
            except Exception as e:
                print(f"Error showing summary: {e}")
        
        # Also show the window
        self.show_window()
    
    def export_data_action(self, item=None):
        """Export data action from tray menu."""
        if "export_data" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["export_data"])
            except Exception as e:
                print(f"Error exporting data: {e}")
        
        # Show window for file dialog
        self.show_window()
    
    def show_settings_action(self, item=None):
        """Show settings action from tray menu."""
        if "show_settings" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["show_settings"])
            except Exception as e:
                print(f"Error showing settings: {e}")
        
        # Show window
        self.show_window()
    
    def show_about_action(self, item=None):
        """Show about dialog from tray menu."""
        try:
            self.root.after(0, self._show_about_dialog)
        except Exception as e:
            print(f"Error showing about dialog: {e}")
    
    def _show_about_dialog(self):
        """Show about dialog in main thread."""
        about_text = f"""{self.app_name}
        
A professional worklog management application for tracking work hours, breaks, and productivity.

Features:
• Work time tracking with 7.5-hour norm
• Break management and monitoring
• Action history with revoke functionality
• Comprehensive export options (CSV, JSON, PDF)
• Advanced settings and customization
• System tray integration
• Keyboard shortcuts
• Automatic backups

Version: 1.0
© 2024 Worklog Manager"""
        
        messagebox.showinfo("About Worklog Manager", about_text)
    
    def quit_application(self, item=None):
        """Quit the application."""
        if "quit_app" in self.callbacks:
            try:
                self.root.after(0, self.callbacks["quit_app"])
            except Exception as e:
                print(f"Error quitting application: {e}")
        else:
            # Fallback quit
            self.root.after(0, self.root.quit)
    
    def is_available(self) -> bool:
        """Check if system tray functionality is available."""
        return PYSTRAY_AVAILABLE
    
    def get_requirements(self) -> List[str]:
        """Get list of required packages for full system tray functionality."""
        requirements = []
        
        if not PYSTRAY_AVAILABLE:
            requirements.append("pystray>=0.19.0")
        
        if not PIL_AVAILABLE:
            requirements.append("Pillow>=8.0.0")
        
        return requirements

class TrayNotification:
    """Handles notifications through the system tray."""
    
    def __init__(self, tray_manager: SystemTrayManager):
        self.tray_manager = tray_manager
        self.notification_queue = []
        self.processing = False
    
    def notify(self, title: str, message: str, notification_type: str = "info", timeout: int = 5):
        """Send a notification through the system tray."""
        notification = {
            'title': title,
            'message': message,
            'type': notification_type,
            'timeout': timeout,
            'timestamp': datetime.now()
        }
        
        self.notification_queue.append(notification)
        
        if not self.processing:
            self.process_notifications()
    
    def process_notifications(self):
        """Process the notification queue."""
        if not self.notification_queue:
            self.processing = False
            return
        
        self.processing = True
        notification = self.notification_queue.pop(0)
        
        # Send notification
        self.tray_manager.show_notification(
            notification['title'],
            notification['message'],
            notification['timeout']
        )
        
        # Schedule next notification
        if self.notification_queue:
            # Wait a bit between notifications to avoid spam
            threading.Timer(2.0, self.process_notifications).start()
        else:
            self.processing = False
    
    def clear_queue(self):
        """Clear all pending notifications."""
        self.notification_queue.clear()
        self.processing = False

class TrayStatusMonitor:
    """Monitors application status and updates tray icon accordingly."""
    
    def __init__(self, tray_manager: SystemTrayManager):
        self.tray_manager = tray_manager
        self.monitor_thread = None
        self.running = False
        
        # Callbacks to get current status
        self.get_work_status = None
        self.get_break_status = None
        self.get_work_start_time = None
    
    def set_status_callbacks(self, get_work_status: Callable, 
                           get_break_status: Callable, 
                           get_work_start_time: Callable):
        """Set callbacks to get current application status."""
        self.get_work_status = get_work_status
        self.get_break_status = get_break_status
        self.get_work_start_time = get_work_start_time
    
    def start_monitoring(self):
        """Start monitoring application status."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring application status."""
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Get current status
                is_working = False
                is_on_break = False
                work_start_time = None
                
                if self.get_work_status:
                    is_working = self.get_work_status()
                
                if self.get_break_status:
                    is_on_break = self.get_break_status()
                
                if self.get_work_start_time:
                    work_start_time = self.get_work_start_time()
                
                # Determine status
                if is_working:
                    if is_on_break:
                        status = "break"
                    else:
                        # Check for overtime
                        if work_start_time:
                            elapsed = datetime.now() - work_start_time
                            if elapsed.total_seconds() > (8 * 3600):  # More than 8 hours
                                status = "overtime"
                            else:
                                status = "working"
                        else:
                            status = "working"
                else:
                    status = "idle"
                
                # Update tray status
                self.tray_manager.update_status(status, work_start_time, is_on_break)
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in tray status monitor: {e}")
                time.sleep(60)  # Wait longer on error
    
    def force_update(self):
        """Force an immediate status update."""
        if self.running and self.monitor_thread:
            # This will cause the next iteration of the loop to run sooner
            pass