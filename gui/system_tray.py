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
import logging
from typing import Optional, Callable, Dict, List
from datetime import datetime
import time
from pathlib import Path

from scripts.packaging.pyinstaller_settings import get_icon

logger = logging.getLogger(__name__)


def _resolve_tray_icon() -> Optional[str]:
    """Return a filesystem path to the preferred tray icon if available."""

    candidates: List[Path] = []

    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable)
        candidates.extend(
            [
                exe_path.with_suffix(".ico"),
                exe_path.parent / "images" / "worklog-manager-tray.ico",
                exe_path.parent / "images" / "worklog-manager-tray.png",
            ]
        )

    icon_value = get_icon("windows")
    if icon_value:
        candidates.append(Path(icon_value))

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base = Path(meipass)
        candidates.extend(
            [
                base / "worklog-manager-tray.ico",
                base / "worklog-manager-tray.png",
                base / "images" / "worklog-manager-tray.ico",
                base / "images" / "worklog-manager-tray.png",
            ]
        )

    module_dir = Path(__file__).resolve().parent
    candidates.extend(
        [
            module_dir.parent / "images" / "worklog-manager-tray.ico",
            module_dir.parent / "images" / "worklog-manager-tray.png",
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file():
            return str(resolved)

    return None

# Try to import pystray for system tray functionality
try:
    import pystray
    from pystray import MenuItem as Item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    logger.warning("pystray not available. System tray functionality will be disabled.")

# Try to import PIL for icon creation
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available. Using fallback tray icon handling.")

class SystemTrayManager:
    """Manages system tray integration for the worklog application."""
    
    def __init__(self, root: tk.Tk, app_name: str = "Worklog Manager", setup_protocol: bool = False):
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

        # Status monitor helper (configurable by application)
        self.status_monitor = TrayStatusMonitor(self)

        # Create default icon
        self.icon_image = self.create_default_icon()
        if self.icon_image is None and not PIL_AVAILABLE:
            logger.warning(
                "System tray icon disabled: Pillow (PIL) is required. Install the 'pillow' package."
            )

        # Setup protocol for window close (optional, controlled by setup_protocol parameter)
        self.original_protocol = None
        if setup_protocol:
            self.setup_window_protocol()
    
    def create_default_icon(self):
        """Create or load the tray icon image."""
        icon_path = _resolve_tray_icon()

        if icon_path and PIL_AVAILABLE:
            try:
                with Image.open(icon_path) as source:
                    return source.copy()
            except Exception:
                logger.debug("Failed to load tray icon from %s", icon_path, exc_info=True)

        if PIL_AVAILABLE:
            size = (64, 64)
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            center = (size[0] // 2, size[1] // 2)
            radius = size[0] // 2 - 4

            draw.ellipse(
                [
                    center[0] - radius,
                    center[1] - radius,
                    center[0] + radius,
                    center[1] + radius,
                ],
                fill="#2c3e50",
                outline="#34495e",
                width=2,
            )

            draw.line(
                [center[0], center[1], center[0], center[1] - radius + 10],
                fill="white",
                width=3,
            )
            draw.line(
                [center[0], center[1], center[0] + radius - 15, center[1]],
                fill="white",
                width=2,
            )

            draw.ellipse(
                [center[0] - 3, center[1] - 3, center[0] + 3, center[1] + 3],
                fill="white",
            )

            return image

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
    
    def on_left_click(self, icon, item):
        """Handle left-click on tray icon - show/hide window."""
        print(f"Left-click detected on tray icon")
        try:
            # Use after() to run in main thread
            print(f"Scheduling toggle_window_visibility in main thread")
            self.root.after(0, self._toggle_window_visibility)
        except Exception as e:
            print(f"Error handling left click: {e}")
            import traceback
            traceback.print_exc()
    
    def _toggle_window_visibility(self):
        """Toggle window visibility (called in main thread)."""
        try:
            print(f"_toggle_window_visibility called")
            if "toggle_window" in self.callbacks:
                print("Using toggle_window callback")
                try:
                    self.callbacks["toggle_window"]()
                    return
                except Exception as callback_error:
                    print(f"toggle_window callback failed: {callback_error}")
                    import traceback
                    traceback.print_exc()
            # Check if window is withdrawn (hidden)
            current_state = self.root.state()
            print(f"Current window state: {current_state}")
            
            if current_state == 'withdrawn':
                # Window is hidden, show it
                print("Window is hidden, showing it...")
                self._show_window_main_thread()
            else:
                # Window is visible, hide it
                print("Window is visible, hiding it...")
                self._hide_window_main_thread()
        except Exception as e:
            print(f"Error toggling window: {e}")
            import traceback
            traceback.print_exc()
            # If error, try to show window
            self._show_window_main_thread()

    def toggle_window_action(self, icon=None, item=None):
        """Toggle window visibility from tray menu/default action."""
        try:
            self.root.after(0, self._toggle_window_visibility)
        except Exception as e:
            print(f"Error toggling window from tray action: {e}")
            import traceback
            traceback.print_exc()
    
    def register_callback(self, action: str, callback: Callable):
        """Register a callback for tray menu actions."""
        self.callbacks[action] = callback
    
    def start_tray(self) -> bool:
        """Start the system tray."""
        if not PYSTRAY_AVAILABLE:
            logger.warning("System tray not available (pystray not installed)")
            return False
        
        if self.running:
            return True
        
        try:
            # Create tray menu
            menu = self.create_tray_menu()
            
            # Create tray icon with left-click handler
            icon_image = self.icon_image or self.create_status_icon("idle")
            
            # Create the icon without default action first
            self.tray_icon = pystray.Icon(
                self.app_name,
                icon_image,
                title=self.app_name
            )
            
            # Set menu
            self.tray_icon.menu = menu
            
            # Set default action (triggered by double-click on most platforms)
            self.tray_icon.default_action = lambda icon, item=None: self.toggle_window_action(icon, item)
            
            logger.info("System tray icon created with default action bound to toggle window")
            
            # Start tray in separate thread
            self.running = True
            self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            self.tray_thread.start()
            
            logger.info("System tray background thread started")
            
            return True
            
        except Exception as e:
            logger.exception("Error starting system tray: %s", e)
            return False
    
    def _run_tray(self):
        """Run the system tray (called in separate thread)."""
        try:
            if self.tray_icon:
                self.tray_icon.run()
        except Exception as e:
            logger.exception("Error running system tray: %s", e)
        finally:
            self.running = False
    
    def stop_tray(self):
        """Stop the system tray."""
        self.running = False
        
        if getattr(self, "status_monitor", None):
            try:
                self.status_monitor.stop_monitoring()
            except Exception as exc:
                logger.debug("Tray status monitor stop failed: %s", exc)

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                logger.exception("Error stopping system tray: %s", e)
        
        if self.tray_thread:
            self.tray_thread.join(timeout=2)

    def cleanup(self):
        """Cleanup helper for main application shutdown."""
        try:
            self.stop_tray()
        except Exception as exc:
            print(f"System tray cleanup failed: {exc}")
    
    def create_tray_menu(self):
        """Create the system tray menu."""
        if not PYSTRAY_AVAILABLE:
            return None
        
        print(f"[SystemTray] Creating menu: current_status='{self.current_status}', is_on_break={self.is_on_break}")
        
        # Note: pystray evaluates 'enabled' at menu display time, which is good
        # The lambda functions will be called each time the menu is shown
        def can_start_work(item):
            result = self.current_status not in ("working", "break")
            print(f"[SystemTray] can_start_work check: current_status='{self.current_status}' -> {result}")
            return result
        
        def can_end_work(item):
            result = self.current_status in ("working", "break")
            print(f"[SystemTray] can_end_work check: current_status='{self.current_status}' -> {result}")
            return result
        
        def can_take_break(item):
            result = self.current_status == "working" and not self.is_on_break
            print(f"[SystemTray] can_take_break check: status='{self.current_status}', is_on_break={self.is_on_break} -> {result}")
            return result
        
        def can_resume_work(item):
            result = self.is_on_break
            print(f"[SystemTray] can_resume_work check: is_on_break={self.is_on_break} -> {result}")
            return result
        
        return pystray.Menu(
            Item("Toggle Window", self.toggle_window_action, default=True),
            Item("Show Window", self.show_window),
            Item("Hide Window", self.hide_window),
            pystray.Menu.SEPARATOR,
            Item("Start Work", self.start_work_action, enabled=can_start_work),
            Item("End Work", self.end_work_action, enabled=can_end_work),
            pystray.Menu.SEPARATOR,
            Item("Take Break", self.take_break_action, enabled=can_take_break),
            Item("Resume Work", self.end_break_action, enabled=can_resume_work),
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
        print(f"[SystemTray] Updating status: status='{status}', is_on_break={is_on_break}")
        
        self.current_status = status

        if isinstance(work_start_time, str):
            try:
                work_start_time = datetime.fromisoformat(work_start_time)
            except Exception:
                work_start_time = None

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
                print(f"[SystemTray] Recreating menu with status='{self.current_status}', is_on_break={self.is_on_break}")
                new_menu = self.create_tray_menu()
                self.tray_icon.menu = new_menu
                try:
                    self.tray_icon.update_menu()
                    print("[SystemTray] Menu updated successfully via update_menu()")
                except Exception as update_error:
                    print(f"[SystemTray] update_menu() failed: {update_error}")
                
            except Exception as e:
                print(f"Error updating tray status: {e}")
                import traceback
                traceback.print_exc()
    
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
    
    def show_notification(self, title: str, message: str = "", timeout: int = 5):
        """Show a system notification through the tray icon."""
        if not PYSTRAY_AVAILABLE:
            return

        if self.tray_icon and self.running:
            try:
                header = self.app_name or "Worklog Manager"
                body_parts = []

                if title:
                    body_parts.append(title)

                if message:
                    body_parts.append(message)

                body = "\n".join(part for part in body_parts if part) or header

                self.tray_icon.notify(body, header)
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
        if "show_window" in self.callbacks:
            print("Delegating show to registered callback")
            try:
                self.callbacks["show_window"]()
                return
            except Exception as callback_error:
                print(f"show_window callback failed: {callback_error}")
                import traceback
                traceback.print_exc()
        print("_show_window_main_thread called")
        print(f"Window state before deiconify: {self.root.state()}")
        self.root.deiconify()
        print(f"Window state after deiconify: {self.root.state()}")
        self.root.lift()
        print("Window lifted")
        self.root.focus_force()
        print("Window focused")
    
    def hide_window(self, item=None):
        """Hide the main application window."""
        try:
            self.root.after(0, self._hide_window_main_thread)
        except Exception as e:
            print(f"Error hiding window: {e}")
    
    def _hide_window_main_thread(self):
        """Hide window in main thread."""
        if "hide_window" in self.callbacks:
            print("Delegating hide to registered callback")
            try:
                self.callbacks["hide_window"]()
                return
            except Exception as callback_error:
                print(f"hide_window callback failed: {callback_error}")
                import traceback
                traceback.print_exc()
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

Version: 1.7.0
© 2025 Worklog Manager"""
        
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
        self.poll_interval = 10  # seconds between status checks
        
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
        # Perform an initial update so tray state is fresh immediately
        try:
            self.force_update()
        except Exception:
            pass
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring application status."""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        self.monitor_thread = None

    def _coerce_start_time(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
        return None

    def _safe_callback(self, callback: Optional[Callable]):
        if not callback:
            return None
        try:
            return callback()
        except Exception as exc:
            print(f"TrayStatusMonitor callback error: {exc}")
            return None

    def _collect_status(self):
        is_working = bool(self._safe_callback(self.get_work_status))
        is_on_break = bool(self._safe_callback(self.get_break_status))
        work_start_time_raw = self._safe_callback(self.get_work_start_time)
        work_start_time = self._coerce_start_time(work_start_time_raw)

        status = "idle"
        if is_working:
            if is_on_break:
                status = "break"
            else:
                status = "working"
                if work_start_time:
                    elapsed = datetime.now() - work_start_time
                    if elapsed.total_seconds() > 8 * 3600:
                        status = "overtime"

        return status, work_start_time, is_on_break
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                status, work_start_time, is_on_break = self._collect_status()
                self.tray_manager.update_status(status, work_start_time, is_on_break)
                
                # Sleep before next check, but exit early if stopped
                for _ in range(self.poll_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                print(f"Error in tray status monitor: {e}")
                time.sleep(max(self.poll_interval, 30))
    
    def force_update(self):
        """Force an immediate status update."""
        try:
            status, work_start_time, is_on_break = self._collect_status()
            self.tray_manager.update_status(status, work_start_time, is_on_break)
        except Exception as exc:
            print(f"TrayStatusMonitor force update failed: {exc}")