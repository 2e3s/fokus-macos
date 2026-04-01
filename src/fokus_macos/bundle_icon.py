from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ICONSET_SPECS = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)


def render_svg_to_png(svg_path: Path, png_path: Path, size: int) -> None:
    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        raise RuntimeError(f"Could not load SVG icon: {svg_path}")

    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    if not image.save(str(png_path)):
        raise RuntimeError(f"Could not write PNG icon: {png_path}")


def build_icns(svg_path: Path, icns_path: Path) -> Path:
    if not svg_path.is_file():
        raise FileNotFoundError(f"Missing SVG icon asset: {svg_path}")

    icns_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fokus-iconset-") as tmp_dir:
        iconset_dir = Path(tmp_dir) / "Fokus.iconset"
        iconset_dir.mkdir()
        for name, size in ICONSET_SPECS:
            render_svg_to_png(svg_path, iconset_dir / name, size)
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
            check=True,
        )
    return icns_path
