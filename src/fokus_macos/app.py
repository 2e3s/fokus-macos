from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from .backend import APP_NAME, APP_ORG, FokusBackend
from .shell import MacOSTrayShell, icon_path


def qml_directory() -> Path:
    return Path(__file__).resolve().parent / "qml"


def ensure_assets_exist() -> None:
    start_icon = icon_path("pomodoro-start-light.svg")
    if not start_icon.is_file():
        raise FileNotFoundError(f"Missing icon assets at {start_icon}")
    if not (qml_directory() / "TimerWindow.qml").is_file():
        raise FileNotFoundError("Missing packaged QML files")


def load_windows(engine: QQmlApplicationEngine) -> None:
    qml_dir = qml_directory()
    for name in ("TimerWindow.qml", "BreakOverlayWindow.qml", "SettingsWindow.qml"):
        engine.load(QUrl.fromLocalFile(str(qml_dir / name)))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    ensure_assets_exist()
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName(APP_ORG)
    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, APP_NAME, "No system tray/menu bar is available on this system.")
        return 1

    backend = FokusBackend(QSettings(APP_ORG, APP_NAME))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Backend", backend)
    engine.rootContext().setContextProperty("AppState", backend.state_map)
    engine.rootContext().setContextProperty("AppDraftSettings", backend.draft_settings_map)
    engine.rootContext().setContextProperty("AppUi", backend.ui_map)
    load_windows(engine)
    if len(engine.rootObjects()) < 3:
        return 1

    tray_shell = MacOSTrayShell(backend, app)
    app._tray_shell = tray_shell
    return app.exec()
