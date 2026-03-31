from __future__ import annotations

import sys
from pathlib import Path


def package_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass) / "fokus_macos"
        return Path(sys.executable).resolve().parent / "fokus_macos"
    return Path(__file__).resolve().parent


def qml_directory() -> Path:
    return package_root() / "qml"


def icon_directory() -> Path:
    return package_root() / "icons"
