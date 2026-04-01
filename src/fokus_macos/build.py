from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fokus_macos.bundle_icon import build_icns


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    spec_path = project_root / "fokus-macos.spec"
    with tempfile.TemporaryDirectory(prefix="fokus-bundle-icon-") as tmp_dir:
        icon_path = build_icns(
            project_root / "src" / "fokus_macos" / "icons" / "pomodoro-start-light.svg",
            Path(tmp_dir) / "Fokus.icns",
        )
        env = dict(os.environ, FOKUS_BUNDLE_ICON=str(icon_path))
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(spec_path),
        ]
        return subprocess.call(command, cwd=project_root, env=env)
