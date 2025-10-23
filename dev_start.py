#!/usr/bin/env python3
"""
Worklog Manager - Development Mode with Auto-Reload

This script runs the Worklog Manager application with file watching enabled.
When you modify any Python file in the project, the application will
automatically restart to reflect your changes.

Usage:
    python dev_start.py
    
    Optional arguments:
    --no-watch    Disable file watching (run normally)
    --verbose     Enable verbose logging for file changes

Requirements:
    pip install watchdog

Author: GitHub Copilot
Version: 1.7.0
"""

import sys
import os
import time
import subprocess
import signal
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Global process handle
app_process: Optional[subprocess.Popen] = None
restart_requested = False


def check_watchdog():
    """Check if watchdog is installed."""
    try:
        import watchdog
        return True
    except ImportError:
        return False


def start_application():
    """Start the main application as a subprocess."""
    global app_process
    
    logger.info("🚀 Starting Worklog Manager...")
    
    # Use the same Python interpreter
    python_exe = sys.executable
    main_script = os.path.join(project_root, 'main.py')
    
    try:
        # On Windows, use CREATE_NEW_PROCESS_GROUP to avoid signal issues
        # Also, don't capture output to avoid deadlocks
        if sys.platform == 'win32':
            app_process = subprocess.Popen(
                [python_exe, main_script],
                cwd=project_root,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            app_process = subprocess.Popen(
                [python_exe, main_script],
                cwd=project_root
            )
        logger.info(f"✓ Application started (PID: {app_process.pid})")
        return app_process
    except Exception as e:
        logger.error(f"✗ Failed to start application: {e}")
        return None


def stop_application():
    """Stop the running application."""
    global app_process
    
    if app_process and app_process.poll() is None:
        logger.info("⏹  Stopping application...")
        try:
            # On Windows, use taskkill for process tree termination
            if sys.platform == 'win32':
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(app_process.pid)],
                        capture_output=True,
                        timeout=3
                    )
                except Exception:
                    # Fallback to terminate if taskkill fails
                    app_process.terminate()
            else:
                # Try graceful shutdown first on Unix
                app_process.terminate()
                
            # Wait for process to end
            try:
                app_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                logger.warning("Application didn't stop gracefully, forcing...")
                app_process.kill()
                app_process.wait()
            logger.info("✓ Application stopped")
        except Exception as e:
            logger.error(f"✗ Error stopping application: {e}")
        finally:
            app_process = None


def restart_application():
    """Restart the application."""
    global restart_requested
    restart_requested = True
    stop_application()
    time.sleep(1.0)  # Longer pause to ensure clean shutdown
    restart_requested = False
    return start_application()


def run_with_watcher(verbose=False):
    """Run the application with file watching enabled."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    except ImportError:
        logger.error("✗ watchdog package not found!")
        logger.error("  Install it with: pip install watchdog")
        return 1
    
    # Track last restart time to avoid multiple rapid restarts
    last_restart_time = 0
    restart_cooldown = 2.0  # seconds - increased to prevent rapid restarts
    
    class ChangeHandler(FileSystemEventHandler):
        """Handle file system events."""
        
        def on_modified(self, event):
            """Handle file modification events."""
            global app_process, restart_requested
            
            # Ignore directory changes
            if event.is_directory:
                return
            
            # Only watch Python files
            if not event.src_path.endswith('.py'):
                return
            
            # Ignore changes in __pycache__, build, backups, etc.
            ignore_dirs = ['__pycache__', 'build', 'backups', 'logs', 'exports', '.git', 'venv', '.venv']
            if any(ignore_dir in event.src_path for ignore_dir in ignore_dirs):
                return
            
            # Check cooldown period
            nonlocal last_restart_time
            current_time = time.time()
            if current_time - last_restart_time < restart_cooldown:
                return
            
            if verbose:
                logger.info(f"📝 File changed: {event.src_path}")
            else:
                logger.info(f"📝 File changed: {Path(event.src_path).name}")
            
            # Restart the application
            if app_process and not restart_requested:
                last_restart_time = current_time
                logger.info("🔄 Restarting application...")
                restart_application()
    
    # Start watching
    event_handler = ChangeHandler()
    observer = Observer()
    
    # Watch the main directories
    watch_dirs = [
        project_root,
        os.path.join(project_root, 'gui'),
        os.path.join(project_root, 'core'),
        os.path.join(project_root, 'utils'),
        os.path.join(project_root, 'exporters'),
    ]
    
    for watch_dir in watch_dirs:
        if os.path.exists(watch_dir):
            observer.schedule(event_handler, watch_dir, recursive=True)
            if verbose:
                logger.info(f"👀 Watching: {watch_dir}")
    
    observer.start()
    logger.info("👀 File watcher enabled - application will auto-reload on changes")
    logger.info("   Press Ctrl+C to stop")
    
    # Start the application
    start_application()
    
    try:
        # Keep the script running and monitor the app process
        while True:
            time.sleep(1)
            
            # Check if app process died unexpectedly
            if app_process and app_process.poll() is not None and not restart_requested:
                exit_code = app_process.returncode
                if exit_code != 0:
                    logger.warning(f"⚠  Application exited with code {exit_code}")
                    logger.info("   Waiting for file changes to restart...")
                else:
                    logger.info("✓ Application exited normally")
                    break
                
    except KeyboardInterrupt:
        logger.info("\n⏹  Stopping development mode...")
    finally:
        # Clean shutdown
        try:
            observer.stop()
            observer.join(timeout=5)
        except Exception as e:
            logger.warning(f"Warning during observer cleanup: {e}")
        
        stop_application()
        logger.info("✓ Development mode stopped")
    
    return 0


def run_without_watcher():
    """Run the application normally without file watching."""
    logger.info("🚀 Starting Worklog Manager (no file watching)...")
    
    # Just run main.py directly
    main_script = os.path.join(project_root, 'main.py')
    
    try:
        import runpy
        runpy.run_path(main_script, run_name='__main__')
        return 0
    except Exception as e:
        logger.error(f"✗ Error running application: {e}")
        return 1


def main():
    """Main entry point."""
    # Parse arguments
    verbose = '--verbose' in sys.argv
    no_watch = '--no-watch' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        return 0
    
    # Check if watchdog is available
    if not no_watch and not check_watchdog():
        logger.warning("⚠  watchdog package not found!")
        logger.warning("   Install it with: pip install watchdog")
        logger.warning("   Running without file watching...")
        no_watch = True
    
    logger.info("=" * 60)
    logger.info("Worklog Manager - Development Mode")
    logger.info("=" * 60)
    
    if no_watch:
        return run_without_watcher()
    else:
        return run_with_watcher(verbose=verbose)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
