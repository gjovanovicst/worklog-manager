"""Shared helpers for Worklog Manager PyInstaller builds."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# Project metadata used across spec files
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
APP_NAME: str = "WorklogManager"
ENTRY_POINT: Path = PROJECT_ROOT / "main.py"

# Optional icon names searched per platform (placeholders can be replaced by the team).
_ICON_CANDIDATES: Dict[str, Sequence[str]] = {
    "windows": ("images/worklog-manager-tray.ico",),
    "macos": ("images/worklog-manager-tray.icns",),
    "linux": (
        "images/worklog-manager-tray.png",
        "images/worklog-manager-tray.ico",
    ),
}


def base_datas() -> List[Tuple[str, str]]:
    """Return data files shipped with every build.

    The tuples follow the PyInstaller (src, dest) convention. Only existing
    files/directories are returned so missing optional assets are ignored.
    """

    candidates: Sequence[Tuple[str, str]] = (
        ("config.ini", "."),
        ("settings.json", "."),
        ("LICENSE", "."),
        ("README.md", "."),
        ("docs", "docs"),
        ("images", "images"),
    )

    datas: List[Tuple[str, str]] = []
    for relative, target in candidates:
        source = PROJECT_ROOT / relative
        if source.exists():
            datas.append((str(source), target))
    return datas


def get_icon(platform_key: str) -> Optional[str]:
    """Return the first existing icon path for the requested platform."""

    for relative in _ICON_CANDIDATES.get(platform_key, ()):  # type: ignore[arg-type]
        candidate = PROJECT_ROOT / relative
        if candidate.exists():
            return str(candidate)
    return None


TARGET_ENV_VAR = "WORKLOG_PACKAGING_TARGET"


def _resolve_target(subdir: str | None = None) -> str | None:
    target = subdir or os.environ.get(TARGET_ENV_VAR)
    return target or None


def dist_path(subdir: str | None = None) -> Path:
    """Return the distribution directory, optionally namespaced per platform."""

    base = PROJECT_ROOT / "dist"
    target = _resolve_target(subdir)
    return base / target if target else base


def build_path(subdir: str | None = None) -> Path:
    """Return the temporary build directory, optionally namespaced per platform."""

    base = PROJECT_ROOT / "build"
    target = _resolve_target(subdir)
    return base / target if target else base
