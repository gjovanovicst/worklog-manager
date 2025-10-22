"""Create desktop shortcuts for packaged Worklog Manager builds."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from pyinstaller_settings import APP_NAME, PROJECT_ROOT, dist_path, get_icon

_SUPPORTED = ("windows", "linux")
_ICON_DEFAULTS = {
    "windows": ("worklog-manager-tray.ico", "worklog-manager-tray.png"),
    "linux": ("worklog-manager-tray.png", "worklog-manager-tray.ico"),
}


@dataclass(frozen=True)
class ShortcutResult:
    """Result details when creating a shortcut."""

    platform: str
    desktop: Path
    applications: Path | None = None


def _detect_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    raise RuntimeError("Shortcut helper currently supports Windows and Linux only.")


def _default_dist_dir() -> Path:
    return dist_path().resolve()


def _resolve_optional_path(candidate: Path | None) -> Path | None:
    if candidate is None:
        return None
    resolved = candidate.expanduser()
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved.resolve()


def _resolve_binary(dist_dir: Path, platform: str) -> Path:
    candidates: list[Path] = []

    if platform == "windows":
        candidates.extend(
            [
                dist_dir / f"{APP_NAME}.exe",
                dist_dir / APP_NAME / f"{APP_NAME}.exe",
            ]
        )
    else:  # linux
        candidates.extend(
            [
                dist_dir / APP_NAME,
                dist_dir / APP_NAME / APP_NAME,
                dist_dir / f"{APP_NAME}.AppImage",
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Could not locate packaged binary under {dist_dir}. Use --binary to point to the executable."
    )


def _default_desktop_dir(platform: str) -> Path:
    home = Path.home()

    if platform == "windows":
        public_candidates: list[Path] = []
        public_root = os.environ.get("PUBLIC")
        if public_root:
            public_candidates.append(Path(public_root) / "Desktop")
        public_candidates.append(Path("C:/Users/Public/Desktop"))

        for candidate in public_candidates:
            if candidate.exists():
                return candidate

        user_candidate = Path(os.environ.get("USERPROFILE", home)) / "Desktop"
        if user_candidate.exists():
            return user_candidate

        # Prefer the common desktop even if it does not exist yet, so we can create it.
        return public_candidates[0] if public_candidates else user_candidate

    for name in ("Desktop", "desktop"):
        candidate = home / name
        if candidate.exists():
            return candidate
    return home


def _default_linux_applications_dir() -> Path:
    return Path.home() / ".local" / "share" / "applications"


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _create_windows_shortcut(
    target: Path,
    icon: Path,
    desktop_dir: Path,
    shortcut_name: str,
    force: bool,
) -> Path:
    shortcut_path = desktop_dir / f"{shortcut_name}.lnk"
    if shortcut_path.exists() and not force:
        raise FileExistsError(f"Shortcut already exists: {shortcut_path}. Use --force to overwrite.")

    _ensure_directory(desktop_dir)

    ps_script = textwrap.dedent(
        f"""
        $ShortcutPath = {json.dumps(str(shortcut_path))}
        $TargetPath = {json.dumps(str(target))}
        $IconPath = {json.dumps(str(icon))}
        $WorkingDir = {json.dumps(str(target.parent))}

        $Shell = New-Object -ComObject WScript.Shell
        $Shortcut = $Shell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $TargetPath
        $Shortcut.WorkingDirectory = $WorkingDir
        $Shortcut.IconLocation = $IconPath
        $Shortcut.Arguments = ""
        $Shortcut.Save()
        """
    )

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_script,
        ],
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError("Failed to create Windows shortcut via PowerShell.")

    return shortcut_path


def _create_linux_shortcut(
    target: Path,
    icon: Path,
    desktop_dir: Path,
    applications_dir: Path,
    shortcut_name: str,
    force: bool,
) -> tuple[Path, Path | None]:
    desktop_entry = textwrap.dedent(
        f"""
        [Desktop Entry]
        Type=Application
        Version=1.0
        Name={shortcut_name}
        Exec={target}
        Icon={icon}
        Terminal=false
        Categories=Utility;
        """
    ).strip()

    desktop_file = desktop_dir / f"{shortcut_name}.desktop"
    applications_file = applications_dir / f"{shortcut_name}.desktop"

    for path in (desktop_file, applications_file):
        if path.exists() and not force:
            raise FileExistsError(f"Shortcut already exists: {path}. Use --force to overwrite.")

    _ensure_directory(desktop_dir)
    _ensure_directory(applications_dir)

    desktop_file.write_text(desktop_entry + "\n", encoding="utf-8")
    desktop_file.chmod(0o755)

    applications_file.write_text(desktop_entry + "\n", encoding="utf-8")
    applications_file.chmod(0o755)

    return desktop_file, applications_file


def _pick_icon(platform: str, target: Path, override: Path | None) -> Path:
    icon_override = _resolve_optional_path(override) if override else None
    if icon_override:
        if icon_override.exists():
            return icon_override
        raise FileNotFoundError(f"Icon path does not exist: {icon_override}")

    icon_value = get_icon(platform)
    if icon_value:
        icon_path = Path(icon_value)
        if icon_path.exists():
            return icon_path.resolve()

    search_roots: list[Path] = []
    if target:
        search_roots.append(target.parent)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        search_roots.append(Path(meipass))
    search_roots.extend([Path.cwd(), PROJECT_ROOT])

    for root in search_roots:
        for name in _ICON_DEFAULTS.get(platform, ()):  # type: ignore[arg-type]
            for candidate in (root / name, root / "images" / name):
                if candidate.exists():
                    return candidate.resolve()

    raise FileNotFoundError("No icon found for desktop shortcut.")


def shortcut_exists(
    platform: str,
    *,
    name: str = APP_NAME,
    desktop_dir: Path | None = None,
    applications_dir: Path | None = None,
) -> bool:
    if platform not in _SUPPORTED:
        raise ValueError(f"Unsupported platform: {platform}")

    desktop_base = _resolve_optional_path(desktop_dir) or _default_desktop_dir(platform)

    if platform == "windows":
        return (desktop_base / f"{name}.lnk").exists()

    applications_base = _resolve_optional_path(applications_dir) or _default_linux_applications_dir()
    return (desktop_base / f"{name}.desktop").exists() or (
        applications_base / f"{name}.desktop"
    ).exists()


def create_shortcut(
    platform: str,
    *,
    dist_dir: Path | None = None,
    binary: Path | None = None,
    desktop_dir: Path | None = None,
    applications_dir: Path | None = None,
    name: str = APP_NAME,
    icon: Path | None = None,
    force: bool = False,
) -> ShortcutResult:
    if platform not in _SUPPORTED:
        raise ValueError(f"Unsupported platform: {platform}")

    target_binary = _resolve_optional_path(binary)
    if target_binary is None:
        resolved_dist = _resolve_optional_path(dist_dir) or _default_dist_dir()
        target_binary = _resolve_binary(resolved_dist, platform)
    else:
        target_binary = target_binary.resolve()

    icon_path = _pick_icon(platform, target_binary, icon)

    if platform == "windows":
        desktop_base = _resolve_optional_path(desktop_dir) or _default_desktop_dir("windows")
        desktop_base = desktop_base.resolve()
        shortcut = _create_windows_shortcut(
            target=target_binary,
            icon=icon_path,
            desktop_dir=desktop_base,
            shortcut_name=name,
            force=force,
        )
        return ShortcutResult(platform=platform, desktop=shortcut)

    desktop_base = _resolve_optional_path(desktop_dir) or _default_desktop_dir("linux")
    desktop_base = desktop_base.resolve()

    applications_base = (
        _resolve_optional_path(applications_dir) or _default_linux_applications_dir()
    ).resolve()

    desktop_file, applications_file = _create_linux_shortcut(
        target=target_binary,
        icon=icon_path,
        desktop_dir=desktop_base,
        applications_dir=applications_base,
        shortcut_name=name,
        force=force,
    )
    return ShortcutResult(platform=platform, desktop=desktop_file, applications=applications_file)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create desktop shortcuts for packaged builds.")
    parser.add_argument(
        "platform",
        nargs="?",
        choices=_SUPPORTED,
        help="Target platform (defaults to the current platform)",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=_default_dist_dir(),
        help="Directory containing packaged artifacts (default: dist/).",
    )
    parser.add_argument(
        "--binary",
        type=Path,
        help="Explicit path to the packaged executable (overrides --dist-dir lookup).",
    )
    parser.add_argument(
        "--desktop-dir",
        type=Path,
        help="Directory where the desktop shortcut should be created.",
    )
    parser.add_argument(
        "--applications-dir",
        type=Path,
        help="Linux only: directory for the .desktop launcher (default: ~/.local/share/applications).",
    )
    parser.add_argument(
        "--name",
        default=APP_NAME,
        help="Display name for the shortcut (default: application name).",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        help="Override the icon path (defaults to images/worklog-manager-tray.*).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing shortcuts if present.",
    )

    args = parser.parse_args(argv)
    if args.platform is None:
        args.platform = _detect_platform()
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        result = create_shortcut(
            platform=args.platform,
            dist_dir=args.dist_dir,
            binary=args.binary,
            desktop_dir=args.desktop_dir,
            applications_dir=args.applications_dir,
            name=args.name,
            icon=args.icon,
            force=args.force,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        raise SystemExit(str(exc)) from exc

    if result.platform == "windows":
        print(f"Created Windows shortcut: {result.desktop}")
    else:
        print(f"Created Linux desktop shortcut: {result.desktop}")
        if result.applications and result.applications != result.desktop:
            print(f"Registered launcher: {result.applications}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
