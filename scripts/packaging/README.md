# Packaging Helpers

This directory contains PyInstaller configuration for producing installable
builds of Worklog Manager on Windows, macOS, and Linux.

## Quick Start

```bash
# Install runtime dependencies (reportlab, plyer, etc.)
pip install -r requirements.txt

# Install packaging dependency
pip install pyinstaller

# Build for the current platform
python scripts/packaging/build.py

# Generate branding assets (optional, requires Pillow)
python scripts/packaging/generate_icons.py
```

Pass a specific platform to generate a different bundle when running on that
operating system:

```bash
python scripts/packaging/build.py windows
python scripts/packaging/build.py macos
python scripts/packaging/build.py linux
```

The resulting artifacts are written to `dist/` with a per-platform layout. For
full instructions— including platform prerequisites, signing guidance, and next
steps for wrapping the binaries as native installers—see `docs/packaging.md`.
