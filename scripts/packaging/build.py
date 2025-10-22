"""Helper script to build Worklog Manager binaries with PyInstaller."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from pyinstaller_settings import APP_NAME, PROJECT_ROOT, TARGET_ENV_VAR, get_icon

_PLATFORM_CHOICES = ("windows", "macos", "linux")
_FPM_FORMATS = {"deb", "rpm", "pacman", "apk", "tar"}
_FPM_TOOL_REQUIREMENTS = {
    "pacman": ("bsdtar", "fakeroot", "gzip"),
    "apk": ("tar", "gzip"),
    "tar": ("tar", "gzip"),
}


def _detect_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(
            "PyInstaller is not installed. Install it with 'pip install pyinstaller'."
        ) from exc


def _build(target: str, clean: bool, log_level: str) -> tuple[int, Path]:
    spec_path = Path(__file__).resolve().parent / f"build_{target}.spec"
    if not spec_path.exists():
        raise SystemExit(f"Missing spec file: {spec_path}")

    dist_dir = PROJECT_ROOT / "dist" / target
    build_dir = PROJECT_ROOT / "build" / target
    dist_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        f"--log-level={log_level}",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
    ]

    if clean:
        command.append("--clean")

    command.append(str(spec_path))

    print("[packaging] Running:", " ".join(command))
    env = os.environ.copy()
    env[TARGET_ENV_VAR] = target

    completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env)
    return completed.returncode, dist_dir


def _derive_version(explicit: str | None) -> str:
    if explicit:
        return explicit

    candidate = PROJECT_ROOT / "main.py"
    try:
        text = candidate.read_text(encoding="utf-8")
    except OSError:
        return "0.0.0"

    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return "0.0.0"


def _ensure_tool(tool: str) -> None:
    if shutil.which(tool) is None:
        raise SystemExit(f"Required tool '{tool}' is not available. Please install it and retry.")


def _run_command(command: list[str], cwd: Path | None = None) -> None:
    print("[packaging] Running:", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _bundle_dir(dist_dir: Path) -> Path:
    bundle = dist_dir / APP_NAME
    if not bundle.exists():
        raise SystemExit(f"Expected bundle directory not found: {bundle}")
    return bundle


def _package_with_fpm(target_format: str, version: str, dist_dir: Path) -> None:
    _ensure_tool("fpm")
    for required in _FPM_TOOL_REQUIREMENTS.get(target_format, ()):  # ensure format-specific tools exist
        _ensure_tool(required)
    bundle = _bundle_dir(dist_dir)
    arch = "amd64"
    extra_args: list[str] = []
    if target_format == "pacman":
        extra_args += ["--pacman-compression", "gz"]
    command = [
        "fpm",
        "-s",
        "dir",
        "-t",
        target_format,
        "-n",
        "worklog-manager",
        "-v",
        version,
        "--architecture",
        arch,
        "--prefix",
        "/opt/worklog-manager",
        "--description",
        "Worklog Manager packaged application",
        *extra_args,
    "--force",
        "-C",
        str(bundle),
        "-p",
        str(dist_dir),
        ".",
    ]
    _run_command(command)


def _package_appimage(version: str, dist_dir: Path) -> None:
    _ensure_tool("appimagetool")
    bundle = _bundle_dir(dist_dir)

    with tempfile.TemporaryDirectory() as tmp:
        app_dir = Path(tmp) / "WorklogManager.AppDir"
        (app_dir / "usr/bin").mkdir(parents=True)
        shutil.copytree(bundle, app_dir / "usr/bin", dirs_exist_ok=True)

        apprun = app_dir / "AppRun"
        apprun.write_text(
            textwrap.dedent(
                """
                #!/bin/sh
                HERE=$(dirname "$0")
                exec "$HERE/usr/bin/WorklogManager.bin" "$@"
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        os.chmod(apprun, 0o755)

        desktop = app_dir / "worklog-manager.desktop"
        desktop.write_text(
            textwrap.dedent(
                """
                [Desktop Entry]
                Type=Application
                Name=Worklog Manager
                Exec=WorklogManager.bin
                Icon=worklog-manager
                Categories=Office;
                Terminal=false
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        icon_path = get_icon("linux")
        if icon_path:
            icon_source = Path(icon_path)
            if icon_source.suffix.lower() == ".png":
                shutil.copy2(icon_source, app_dir / "worklog-manager.png")

        output = dist_dir / f"WorklogManager-{version}-x86_64.AppImage"
        _run_command(["appimagetool", str(app_dir), str(output)])


def _package_tarball(version: str, dist_dir: Path) -> None:
    bundle = _bundle_dir(dist_dir)
    arch = "amd64"
    output = dist_dir / f"worklog-manager_{version}_{arch}.tar.gz"
    _run_command(
        ["tar", "-czf", str(output), "-C", str(bundle.parent), bundle.name],
    )


def _package_linux(formats: set[str], version: str, dist_dir: Path) -> None:
    for fmt in sorted(formats):
        if fmt == "tar":
            # FPM's tar output doesn't support extra compression flags reliably; create manually
            _package_tarball(version, dist_dir)
        elif fmt in _FPM_FORMATS:
            _package_with_fpm(fmt, version, dist_dir)
        elif fmt == "appimage":
            _package_appimage(version, dist_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package Worklog Manager with PyInstaller")
    parser.add_argument(
        "target",
        nargs="?",
        choices=_PLATFORM_CHOICES,
        help="Target platform spec to use (defaults to current platform)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip the PyInstaller --clean pass",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"),
        help="Set PyInstaller log level",
    )
    parser.add_argument(
        "--package",
        dest="package_formats",
        action="append",
        choices=("deb", "rpm", "pacman", "apk", "tar", "appimage"),
        help="Produce additional Linux packages using the given format (repeatable)",
    )
    parser.add_argument(
        "--package-version",
        dest="package_version",
        help="Override the package version (defaults to the application version)",
    )

    args = parser.parse_args(argv)

    _ensure_pyinstaller()

    detected = _detect_platform()
    target = args.target or detected
    if target != detected:
        raise SystemExit(
            f"Cross-platform packaging is not supported: requested '{target}' while running on '{detected}'."
            " Run the build on the target operating system or use a suitable container/VM."
        )
    clean = not args.no_clean

    if args.package_formats and target != "linux":
        raise SystemExit("Additional packaging formats are only supported for Linux builds.")

    exit_code, dist_dir = _build(target=target, clean=clean, log_level=args.log_level)
    if exit_code != 0:
        return exit_code

    if target == "linux" and args.package_formats:
        version = _derive_version(args.package_version)
        _package_linux(set(args.package_formats), version, dist_dir)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
