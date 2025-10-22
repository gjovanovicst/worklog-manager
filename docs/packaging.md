# Packaging Guide

This guide describes how to build distributable Worklog Manager binaries for
Windows, macOS, and Linux using PyInstaller.

## Overview

The repository now ships with per-platform PyInstaller spec files and a helper
script located in `scripts/packaging/`. These builds produce self-contained
folders that bundle Python, application code, default configuration, and the
core documentation set.

## Prerequisites

1. **Install application dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Install packaging tooling**
   ```bash
   pip install pyinstaller
   ```
3. **Platform-specific notes**
   - **Windows**: Build on Windows 10/11. Install the Visual C++ build tools if
     not already present (bundled with the Python.org installer). Optional: UPX
     if you want smaller binaries.
   - **macOS**: Build on macOS 12+ with Xcode command line tools. Codesign and
     notarization require an Apple Developer ID.
   - **Linux**: Build on a recent distribution (Ubuntu 22.04+, Fedora 38+, etc.)
     with the system toolchain. For AppImage generation you will additionally
     need `appimagetool` (not included here).

## Building Binaries

Run the helper script from the project root. When no target is supplied the
script infers the current platform.

```bash
python scripts/packaging/build.py
```

Specify a target explicitly when necessary:

```bash
python scripts/packaging/build.py windows
python scripts/packaging/build.py macos
python scripts/packaging/build.py linux
```

Optional flags:

- `--no-clean` &mdash; reuse the previous PyInstaller work directory
- `--log-level` &mdash; adjust PyInstaller verbosity (`TRACE|DEBUG|INFO|WARN|ERROR|CRITICAL`)

Each command produces artifacts under `dist/`:

| Platform | Output | Contents |
|----------|--------|----------|
| Windows  | `dist/WorklogManager/WorklogManager.exe` | Executable + supporting files |
| macOS    | `dist/WorklogManager.app`               | `.app` bundle ready for signing |
| Linux    | `dist/WorklogManager/WorklogManager`    | ELF binary within an onedir folder |

The default build copies `config.ini`, `settings.json`, `LICENSE`, `README.md`,
and the `docs/` and `images/` directories alongside the binary. Place platform
icons in `images/worklog-manager-tray.ico` (Windows),
`images/worklog-manager-tray.icns` (macOS), or
`images/worklog-manager-tray.png` (Linux) to embed custom branding. PyInstaller
spec files call `get_icon()` from `pyinstaller_settings.py`, so the first
matching asset in `images/` is automatically embedded in the executable. A
helper at `python scripts/packaging/generate_icons.py` uses Pillow to create
consistent tray-style clock assets (ICO, ICNS, and sized PNGs). On macOS, if the
ICNS file cannot be written automatically, run `iconutil -c icns images`
against the generated PNG set.

## Desktop Shortcuts

After packaging you can generate desktop launchers that reuse the bundled icon:

```bash
# Windows (creates WorklogManager.lnk on the current user's desktop)
python scripts/packaging/create_shortcuts.py windows

# Linux (drops WorklogManager.desktop on ~/Desktop and registers it)
python scripts/packaging/create_shortcuts.py linux
```

Key options:

- `--desktop-dir` &mdash; override the destination desktop folder (defaults to the
  current user's desktop).
- `--binary` &mdash; point at a specific executable when the helper cannot infer it.
- `--icon` &mdash; supply an alternate icon path if you do not want to reuse the
  default file from `images/`.
- `--force` &mdash; overwrite an existing shortcut.

Linux invokes both the desktop file (`~/Desktop/WorklogManager.desktop`) and a
launcher in `~/.local/share/applications/` so the app surfaces in the shell
menus. Windows uses PowerShell to emit a `.lnk` with the embedded ICO.

## Post-Build Steps

- **Windows installers**: Wrap the `dist/WorklogManager` folder with Inno Setup,
  WiX Toolset, or MSIX to provide installers in addition to the generated
  desktop shortcut.
- **macOS distribution**: Codesign the `.app`, create a notarized DMG or PKG,
  and staple the notarization ticket before publishing.
- **Linux packaging**: Convert the onedir output into an AppImage, `.deb`, or
  `.rpm` using tools such as `appimagetool`, `fpm`, or `dpkg-deb`.

## Continuous Integration

Automate packaging through GitHub Actions or another CI runner:

1. Install dependencies (`pip install -r requirements.txt pyinstaller`).
2. Run `python scripts/packaging/build.py` on each OS matrix job.
3. Upload artifacts from the `dist/` directory to the workflow summary and/or
   attach them to GitHub Releases.
4. Store signing certificates and credentials securely in repository secrets.

With these steps you can consistently produce installable builds for all three
platforms and extend the pipeline to handle signing and installer generation as
needed.
