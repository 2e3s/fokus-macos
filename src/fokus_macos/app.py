from __future__ import annotations

import logging
import plistlib
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QSettings, Qt, QTimer, Signal, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QFont, QFontDatabase, QIcon, QWheelEvent
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


LOGGER = logging.getLogger("fokus_macos")
APP_ORG = "com.dv"
APP_NAME = "Fokus"
LAUNCH_AGENT_ID = "com.dv.fokus.macos"
DEFAULT_BEEP_TIMEOUT_MS = 6000
def icon_directory() -> Path:
    return Path(__file__).resolve().parent / "icons"


def icon_path(name: str) -> Path:
    return icon_directory() / name


def available_icon(frame: Optional[int]) -> QIcon:
    if frame is None:
        return QIcon(str(icon_path("pomodoro-start-light.svg")))
    return QIcon(str(icon_path(f"pomodoro-indicator-light-{frame:02d}.svg")))


def launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"


@dataclass
class AppSettings:
    focus_time: int = 25
    short_break_time: int = 5
    long_break_time: int = 20
    ticking_time: int = 10
    number_of_sessions: int = 4
    flow_divisor: int = 3
    clock_fontfamily: str = ""
    timer_start_notification_enabled: bool = False
    timer_end_notification_enabled: bool = True
    timer_start_sfx_enabled: bool = False
    timer_start_sfx_filepath: str = ""
    timer_stop_sfx_enabled: bool = True
    timer_stop_sfx_filepath: str = ""
    timer_tick_sfx_enabled: bool = False
    timer_tick_sfx_filepath: str = ""
    timer_auto_focus_enabled: bool = False
    timer_auto_pause_enabled: bool = False
    start_focus_script_filepath: str = ""
    start_focus_script_enabled: bool = False
    start_break_script_filepath: str = ""
    start_break_script_enabled: bool = False
    end_focus_script_filepath: str = ""
    end_focus_script_enabled: bool = False
    end_break_script_filepath: str = ""
    end_break_script_enabled: bool = False
    stop_script_filepath: str = ""
    stop_script_enabled: bool = False
    show_icon_in_compact_mode: bool = True
    show_time_in_compact_mode: bool = False
    show_fullscreen_break: bool = True
    flowmodoro_mode_enabled: bool = False
    autostart: bool = False
    fullscreen_buttons_postpone: bool = True
    fullscreen_buttons_skip: bool = True
    fullscreen_buttons_close: bool = True
    do_not_disturb_enabled: bool = False
    show_buttons_on_hover: bool = False

    @classmethod
    def load(cls, qsettings: QSettings) -> "AppSettings":
        values: dict[str, object] = {}
        defaults = cls()
        for item in fields(cls):
            default = getattr(defaults, item.name)
            values[item.name] = qsettings.value(item.name, defaultValue=default, type=type(default))
        return cls(**values)

    def save(self, qsettings: QSettings) -> None:
        for key, value in asdict(self).items():
            qsettings.setValue(key, value)
        qsettings.sync()


class SoundManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.effect = QSoundEffect(self)

    def preview(self, path: str) -> None:
        self.play(path, fallback_beep=True)

    def play(self, path: str, *, volume: float = 1.0, fallback_beep: bool = False) -> None:
        sound_path = Path(path).expanduser()
        if sound_path.is_file():
            self.effect.stop()
            self.effect.setSource(QUrl.fromLocalFile(str(sound_path)))
            self.effect.setVolume(max(0.0, min(1.0, volume)))
            self.effect.play()
            return
        if fallback_beep:
            QApplication.beep()


class ScriptRunner(QObject):
    def run_if_enabled(self, enabled: bool, path: str) -> None:
        if not enabled or not path.strip():
            return
        script_path = Path(path).expanduser()
        if not script_path.is_file():
            LOGGER.warning("Script file does not exist: %s", script_path)
            return
        try:
            subprocess.Popen(
                ["/bin/sh", str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            LOGGER.exception("Failed to run script: %s", script_path)


class MacOSIntegration(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._dnd_enabled = False

    def set_do_not_disturb(self, enabled: bool) -> None:
        self._dnd_enabled = enabled
        if enabled:
            LOGGER.info("Do Not Disturb integration is not automated; use scripts for custom macOS Focus handling.")

    def sync_autostart(self, enabled: bool) -> None:
        target = launch_agent_path()
        if enabled:
            target.parent.mkdir(parents=True, exist_ok=True)
            plist = {
                "Label": LAUNCH_AGENT_ID,
                "RunAtLoad": True,
                "ProcessType": "Interactive",
                "ProgramArguments": self.program_arguments(),
                "WorkingDirectory": str(Path.home()),
            }
            with target.open("wb") as handle:
                plistlib.dump(plist, handle, sort_keys=True)
        elif target.exists():
            target.unlink()

    @staticmethod
    def program_arguments() -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable]

        argv0 = Path(sys.argv[0]).resolve()
        if argv0.is_file():
            return [sys.executable, str(argv0)]
        return [sys.executable, "-m", "fokus_macos"]


class TimerEngine(QObject):
    updated = Signal()
    phase_completed = Signal(str)
    start_notification = Signal(str)
    end_notification = Signal(str)

    def __init__(self, settings: AppSettings, scripts: ScriptRunner, integration: MacOSIntegration) -> None:
        super().__init__()
        self.settings = settings
        self.scripts = scripts
        self.integration = integration
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._set_time)
        self.state_val = 1
        self.status_text = "focus"
        self.initial_seconds = 0
        self.counter_seconds = 0
        self.counter_milliseconds = 0
        self.previous_ms = 0
        self.reset_time()

    @property
    def running(self) -> bool:
        return self.timer.isActive()

    def is_break(self) -> bool:
        return self.state_val % 2 == 0

    def set_settings(self, settings: AppSettings) -> None:
        mode_changed = self.settings.flowmodoro_mode_enabled != settings.flowmodoro_mode_enabled
        focus_changed = self.settings.focus_time != settings.focus_time
        self.settings = settings
        if mode_changed or focus_changed:
            self.stop()
            return
        if not self.running:
            self.reset_time()
        self.updated.emit()

    def format_counter(self) -> str:
        sec = self.counter_seconds % 60
        minutes_total = self.counter_seconds // 60
        minutes = minutes_total % 60
        hours = minutes_total // 60
        if hours > 0:
            return f"{hours:01d}:{minutes:02d}:{sec:02d}"
        return f"{minutes:02d}:{sec:02d}"

    def tooltip_text(self) -> str:
        if not self.running:
            return ""
        if self.state_val == 2 * self.settings.number_of_sessions:
            return "Take a long break!"
        if self.is_break():
            return "Go for a walk."
        return "Focus on your work!"

    def tray_frame(self) -> Optional[int]:
        if not self.running:
            return None
        if self.initial_seconds <= 0:
            return 61
        ratio = max(0.0, min(1.0, self.counter_seconds / self.initial_seconds))
        return max(0, min(61, round(ratio * 61)))

    def current_session_index(self) -> int:
        return ((self.state_val - 1) // 2) + 1

    def primary_action_text(self) -> str:
        if not self.running:
            return "Start"
        if self.settings.flowmodoro_mode_enabled and not self.is_break():
            return "Stop Focus"
        if self.settings.flowmodoro_mode_enabled and self.is_break():
            return "Skip Break"
        return "Pause"

    def secondary_action_text(self) -> str:
        return "Reset" if self.settings.flowmodoro_mode_enabled else "Stop"

    def set_initial_seconds(self) -> int:
        if self.settings.flowmodoro_mode_enabled and not self.is_break():
            return 0
        return self.settings.focus_time * 60

    def start(self) -> None:
        if self.settings.timer_start_notification_enabled:
            self.start_notification.emit(self.notification_summary(is_start=True))
        if not self.is_break():
            self.integration.set_do_not_disturb(self.settings.do_not_disturb_enabled)
        self.previous_ms = 0
        self.execute_script("start")
        self.timer.start()
        self.updated.emit()

    def pause(self) -> None:
        self.integration.set_do_not_disturb(False)
        self.timer.stop()
        self.updated.emit()

    def activate_primary(self) -> None:
        if not self.running:
            self.start()
            return
        if self.settings.flowmodoro_mode_enabled:
            self.skip()
            return
        self.pause()

    def stop(self) -> None:
        self.integration.set_do_not_disturb(False)
        self.execute_script("stop")
        self.timer.stop()
        self.state_val = 1
        self.reset_time()
        self.updated.emit()

    def postpone(self) -> None:
        if not self.is_break():
            return
        self.prev_state()
        self.status_text = "focus"
        self.initial_seconds = self.settings.focus_time * 60
        self.counter_seconds = 5 * 60
        self.counter_milliseconds = self.counter_seconds * 1000
        self.previous_ms = 0
        self.updated.emit()

    def skip(self) -> None:
        self.next_state()
        self.reset_time()
        if not self.is_break():
            self.integration.set_do_not_disturb(self.settings.do_not_disturb_enabled)
        else:
            self.integration.set_do_not_disturb(False)
        self.updated.emit()

    def shift_counter(self, seconds: int) -> None:
        if self.settings.flowmodoro_mode_enabled:
            return
        if self.counter_seconds + seconds <= 0:
            return
        self.counter_milliseconds += seconds * 1000
        self.counter_seconds += seconds
        self.initial_seconds += seconds
        self.updated.emit()

    def reset_time(self) -> None:
        if self.settings.flowmodoro_mode_enabled and not self.is_break():
            self.initial_seconds = 0
            self.status_text = "flow"
        elif self.settings.flowmodoro_mode_enabled and self.is_break():
            self.initial_seconds = max(1, self.counter_seconds // max(1, self.settings.flow_divisor))
            self.status_text = "flow break"
        elif self.state_val == 2 * self.settings.number_of_sessions:
            self.initial_seconds = self.settings.long_break_time * 60
            self.status_text = "long break"
        elif self.is_break():
            self.initial_seconds = self.settings.short_break_time * 60
            self.status_text = "short break"
        else:
            self.initial_seconds = self.settings.focus_time * 60
            self.status_text = "focus"
        self.counter_seconds = self.initial_seconds
        self.counter_milliseconds = self.counter_seconds * 1000
        self.previous_ms = 0
        self.updated.emit()

    def next_state(self) -> None:
        if self.state_val < self.settings.number_of_sessions * 2:
            self.state_val += 1
        else:
            self.state_val = 1

        if self.state_val == 2 * self.settings.number_of_sessions and self.settings.long_break_time == 0:
            self.next_state()
        elif self.is_break() and self.settings.short_break_time == 0:
            self.next_state()

    def prev_state(self) -> None:
        if self.state_val != 1:
            self.state_val -= 1

    def notification_summary(self, *, is_start: bool) -> str:
        if is_start:
            if self.state_val == 2 * self.settings.number_of_sessions:
                return "Take a long break!"
            if self.is_break():
                return "Go for a walk."
            return "Focus on your work!"
        if self.is_break():
            return "End of break."
        return "End of focus time."

    def execute_script(self, phase: str) -> None:
        if phase == "stop":
            self.scripts.run_if_enabled(self.settings.stop_script_enabled, self.settings.stop_script_filepath)
            return
        if phase == "start":
            if self.is_break():
                self.scripts.run_if_enabled(
                    self.settings.start_break_script_enabled,
                    self.settings.start_break_script_filepath,
                )
            else:
                self.scripts.run_if_enabled(
                    self.settings.start_focus_script_enabled,
                    self.settings.start_focus_script_filepath,
                )
            return
        if phase == "end":
            if self.is_break():
                self.scripts.run_if_enabled(
                    self.settings.end_break_script_enabled,
                    self.settings.end_break_script_filepath,
                )
            else:
                self.scripts.run_if_enabled(
                    self.settings.end_focus_script_enabled,
                    self.settings.end_focus_script_filepath,
                )

    def _set_time(self) -> None:
        current_ms = self._now_ms()
        if self.previous_ms == 0:
            self.previous_ms = current_ms
            return
        delta = current_ms - self.previous_ms
        self.previous_ms = current_ms
        old_counter_seconds = (self.counter_milliseconds + 999) // 1000

        if self.settings.flowmodoro_mode_enabled and not self.is_break():
            self.counter_milliseconds += delta
        else:
            self.counter_milliseconds -= delta

        new_counter_seconds = (self.counter_milliseconds + 999) // 1000
        if new_counter_seconds == old_counter_seconds:
            return

        if self.settings.flowmodoro_mode_enabled and not self.is_break():
            self.counter_seconds += 1
        else:
            self.counter_seconds -= 1
            if self.counter_seconds <= 0:
                self._end()
                return
        self.updated.emit()

    def _end(self) -> None:
        self.integration.set_do_not_disturb(False)
        if self.settings.timer_end_notification_enabled:
            self.end_notification.emit(self.notification_summary(is_start=False))
        self.execute_script("end")
        self.timer.stop()
        completed_status = self.status_text
        self.next_state()
        self.reset_time()
        self.phase_completed.emit(completed_status)
        auto_continue = (
            self.is_break() and self.settings.timer_auto_pause_enabled
        ) or (
            not self.is_break() and self.settings.timer_auto_focus_enabled
        )
        if auto_continue:
            self.start()
        else:
            self.updated.emit()

    @staticmethod
    def _now_ms() -> int:
        return int(time.monotonic() * 1000)


class TimerWindow(QMainWindow):
    def __init__(self, app: "FokusApp") -> None:
        super().__init__()
        self.app = app
        self.wheel_delta = 0
        self.setWindowTitle("Fokus")
        self.setMinimumSize(360, 240)
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self.session_label = QLabel()
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setStyleSheet("font-size: 14px; color: palette(mid);")
        root.addWidget(self.session_label)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 56px; font-weight: 600;")
        root.addWidget(self.time_label)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px;")
        root.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        root.addLayout(buttons)

        self.primary_button = QPushButton()
        self.primary_button.clicked.connect(self.app.engine.activate_primary)
        buttons.addWidget(self.primary_button)

        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self.app.engine.skip)
        buttons.addWidget(self.skip_button)

        self.postpone_button = QPushButton("Postpone")
        self.postpone_button.clicked.connect(self.app.engine.postpone)
        buttons.addWidget(self.postpone_button)

        self.secondary_button = QPushButton()
        self.secondary_button.clicked.connect(self.app.engine.stop)
        buttons.addWidget(self.secondary_button)

        root.addStretch(1)
        self.refresh()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.adjust_by_wheel_delta(event.angleDelta().y() or event.pixelDelta().y()):
            event.accept()
            return
        super().wheelEvent(event)

    def adjust_by_wheel_delta(self, event_delta: int) -> bool:
        if self.app.settings.flowmodoro_mode_enabled or event_delta == 0:
            return False

        self.wheel_delta += event_delta
        increment = 0

        while self.wheel_delta >= 120:
            self.wheel_delta -= 120
            increment += 1

        while self.wheel_delta <= -120:
            self.wheel_delta += 120
            increment -= 1

        while increment != 0:
            self.app.engine.shift_counter(60 if increment > 0 else -60)
            increment += -1 if increment > 0 else 1

        return True

    def refresh(self) -> None:
        engine = self.app.engine
        settings = self.app.settings
        self.session_label.setText(
            f"Session {engine.current_session_index()} / {settings.number_of_sessions}"
            if not settings.flowmodoro_mode_enabled
            else "Flowmodoro"
        )
        self.time_label.setText(engine.format_counter())
        font_family = settings.clock_fontfamily.strip()
        if font_family:
            font = QFont(font_family)
            font.setPointSize(38)
            self.time_label.setFont(font)
        self.status_label.setText(engine.status_text.title())
        self.primary_button.setText(engine.primary_action_text())
        self.secondary_button.setText(engine.secondary_action_text())
        self.skip_button.setVisible(not settings.flowmodoro_mode_enabled)
        self.postpone_button.setVisible(engine.is_break())


class BreakOverlay(QWidget):
    def __init__(self, app: "FokusApp") -> None:
        super().__init__(None)
        self.app = app
        self.setWindowTitle("Break")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setStyleSheet(
            "background-color: rgba(20, 20, 20, 220); color: white;"
            "QPushButton { min-width: 120px; padding: 8px 12px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 48, 48, 48)
        root.setSpacing(24)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 80px; font-weight: 700;")
        root.addWidget(self.time_label, 1)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 28px;")
        root.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignCenter)
        buttons.setSpacing(16)
        root.addLayout(buttons)

        self.postpone_button = QPushButton("Postpone")
        self.postpone_button.clicked.connect(self.app.engine.postpone)
        buttons.addWidget(self.postpone_button)

        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self.app.engine.skip)
        buttons.addWidget(self.skip_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.hide)
        buttons.addWidget(self.close_button)

    def refresh(self) -> None:
        settings = self.app.settings
        engine = self.app.engine
        self.time_label.setText(engine.format_counter())
        self.status_label.setText(engine.status_text.title())
        self.postpone_button.setVisible(engine.is_break() and settings.fullscreen_buttons_postpone)
        self.skip_button.setVisible(engine.is_break() and settings.fullscreen_buttons_skip)
        self.close_button.setVisible(engine.is_break() and settings.fullscreen_buttons_close)

        font_family = settings.clock_fontfamily.strip()
        if font_family:
            font = QFont(font_family)
            font.setPointSize(56)
            self.time_label.setFont(font)

    def sync_visibility(self) -> None:
        if not self.app.settings.show_fullscreen_break:
            self.hide()
            return
        if self.app.engine.is_break() and self.app.engine.running:
            screen = QApplication.primaryScreen()
            if screen is not None:
                self.setGeometry(screen.geometry())
            self.showFullScreen()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()


class SettingsDialog(QDialog):
    def __init__(self, app: "FokusApp") -> None:
        super().__init__(None)
        self.app = app
        self.setWindowTitle("Fokus Settings")
        self.setMinimumWidth(640)
        self._controls: dict[str, QWidget] = {}

        root = QVBoxLayout(self)
        tabs = QTabWidget(self)
        root.addWidget(tabs)

        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._timer_tab(), "Timer")
        tabs.addTab(self._notifications_tab(), "Notifications")
        tabs.addTab(self._scripts_tab(), "Scripts")

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Save")
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _general_tab(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)
        layout.addRow("Timer font", self._font_box("clock_fontfamily"))
        layout.addRow("", self._check("show_icon_in_compact_mode", "Show icon in menu bar"))
        layout.addRow("", self._check("show_time_in_compact_mode", "Show time in menu bar"))
        layout.addRow("", self._check("autostart", "Launch at login"))
        layout.addRow("", self._check("do_not_disturb_enabled", "Enable Do Not Disturb during focus"))
        layout.addRow("", self._check("timer_auto_focus_enabled", "Auto-start focus sessions"))
        layout.addRow("", self._check("timer_auto_pause_enabled", "Auto-start break sessions"))
        layout.addRow("", self._check("show_fullscreen_break", "Show fullscreen break overlay"))
        layout.addRow("", self._check("fullscreen_buttons_postpone", "Overlay shows Postpone"))
        layout.addRow("", self._check("fullscreen_buttons_skip", "Overlay shows Skip"))
        layout.addRow("", self._check("fullscreen_buttons_close", "Overlay shows Close"))
        layout.addRow("", self._check("show_buttons_on_hover", "Only show overlay buttons on hover"))
        layout.addRow("", self._check("flowmodoro_mode_enabled", "Enable Flowmodoro mode"))
        return page

    def _timer_tab(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)
        layout.addRow("Number of sessions", self._spin("number_of_sessions", 1, 10))
        layout.addRow("Focus minutes", self._spin("focus_time", 1, 9999))
        layout.addRow("Short break minutes", self._spin("short_break_time", 0, 9999))
        layout.addRow("Long break minutes", self._spin("long_break_time", 0, 9999))
        layout.addRow("Ticking time (seconds)", self._spin("ticking_time", 0, 60))
        layout.addRow("Flow divisor", self._spin("flow_divisor", 1, 9999))
        return page

    def _notifications_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._check("timer_start_notification_enabled", "Show start notification"))
        layout.addWidget(self._sound_row("timer_start_sfx_enabled", "timer_start_sfx_filepath", "Play start sound"))
        layout.addSpacing(12)
        layout.addWidget(self._check("timer_end_notification_enabled", "Show end notification"))
        layout.addWidget(self._sound_row("timer_stop_sfx_enabled", "timer_stop_sfx_filepath", "Play end sound"))
        layout.addSpacing(12)
        layout.addWidget(self._sound_row("timer_tick_sfx_enabled", "timer_tick_sfx_filepath", "Play ticking sound"))
        layout.addStretch(1)
        return page

    def _scripts_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._script_row("start_focus_script_enabled", "start_focus_script_filepath", "Start focus script"))
        layout.addWidget(self._script_row("start_break_script_enabled", "start_break_script_filepath", "Start break script"))
        layout.addWidget(self._script_row("end_focus_script_enabled", "end_focus_script_filepath", "End focus script"))
        layout.addWidget(self._script_row("end_break_script_enabled", "end_break_script_filepath", "End break script"))
        layout.addWidget(self._script_row("stop_script_enabled", "stop_script_filepath", "Stop/reset script"))
        layout.addStretch(1)
        return page

    def _spin(self, key: str, minimum: int, maximum: int) -> QSpinBox:
        control = QSpinBox()
        control.setRange(minimum, maximum)
        control.setValue(getattr(self.app.settings, key))
        self._controls[key] = control
        return control

    def _check(self, key: str, label: str) -> QCheckBox:
        control = QCheckBox(label)
        control.setChecked(bool(getattr(self.app.settings, key)))
        self._controls[key] = control
        return control

    def _font_box(self, key: str) -> QComboBox:
        control = QComboBox()
        control.addItem("Default", "")
        for family in QFontDatabase().families():
            control.addItem(family, family)
        current = getattr(self.app.settings, key)
        index = control.findData(current)
        control.setCurrentIndex(max(0, index))
        self._controls[key] = control
        return control

    def _file_input(
        self,
        key: str,
        button_text: str,
        preview: Optional[Callable[[str], None]] = None,
    ) -> QWidget:
        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit(getattr(self.app.settings, key))
        self._controls[key] = line_edit
        row.addWidget(line_edit, 1)

        browse = QPushButton(button_text)
        browse.clicked.connect(lambda: self._pick_file(line_edit))
        row.addWidget(browse)

        if preview is not None:
            play = QPushButton("Preview")
            play.clicked.connect(lambda: preview(line_edit.text()))
            row.addWidget(play)
        return wrapper

    def _sound_row(self, enabled_key: str, path_key: str, label: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._check(enabled_key, label))
        layout.addWidget(self._file_input(path_key, "Choose Sound", self.app.sound_manager.preview))
        return wrapper

    def _script_row(self, enabled_key: str, path_key: str, label: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._check(enabled_key, label))
        layout.addWidget(self._file_input(path_key, "Choose Script"))
        return wrapper

    def _pick_file(self, line_edit: QLineEdit) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Choose File", str(Path.home()))
        if filename:
            line_edit.setText(filename)

    def _save(self) -> None:
        values: dict[str, object] = {}
        for item in fields(AppSettings):
            control = self._controls[item.name]
            if isinstance(control, QSpinBox):
                values[item.name] = control.value()
            elif isinstance(control, QCheckBox):
                values[item.name] = control.isChecked()
            elif isinstance(control, QLineEdit):
                values[item.name] = control.text().strip()
            elif isinstance(control, QComboBox):
                values[item.name] = control.currentData()
        settings = AppSettings(**values)
        if settings.flowmodoro_mode_enabled:
            settings.fullscreen_buttons_postpone = False
        self.app.apply_settings(settings)
        self.accept()


class FokusApp(QObject):
    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self.qt_app = qt_app
        self.qsettings = QSettings(APP_ORG, APP_NAME)
        self.settings = AppSettings.load(self.qsettings)
        self.sound_manager = SoundManager()
        self.script_runner = ScriptRunner()
        self.integration = MacOSIntegration()
        self.engine = TimerEngine(self.settings, self.script_runner, self.integration)
        self.engine.updated.connect(self.refresh_ui)
        self.engine.start_notification.connect(lambda message: self.notify(message, start=True))
        self.engine.end_notification.connect(lambda message: self.notify(message, start=False))

        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Fokus")
        self.tray.activated.connect(self._handle_tray_activation)
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)

        self.time_action = QAction("", self.menu)
        self.time_action.setEnabled(False)
        self.status_action = QAction("", self.menu)
        self.status_action.setEnabled(False)

        self.primary_action = QAction(self.menu)
        self.primary_action.triggered.connect(self.engine.activate_primary)
        self.skip_action = QAction("Skip", self.menu)
        self.skip_action.triggered.connect(self.engine.skip)
        self.postpone_action = QAction("Postpone", self.menu)
        self.postpone_action.triggered.connect(self.engine.postpone)
        self.secondary_action = QAction(self.menu)
        self.secondary_action.triggered.connect(self.engine.stop)
        self.open_action = QAction("Open Timer Window", self.menu)
        self.open_action.triggered.connect(self.show_timer_window)
        self.settings_action = QAction("Settings…", self.menu)
        self.settings_action.triggered.connect(self.show_settings)
        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(self.qt_app.quit)

        self.menu.addAction(self.time_action)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()
        self.menu.addAction(self.primary_action)
        self.menu.addAction(self.skip_action)
        self.menu.addAction(self.postpone_action)
        self.menu.addAction(self.secondary_action)
        self.menu.addSeparator()
        self.menu.addAction(self.open_action)
        self.menu.addAction(self.settings_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.timer_window = TimerWindow(self)
        self.overlay = BreakOverlay(self)
        self.settings_dialog: Optional[SettingsDialog] = None

        self.integration.sync_autostart(self.settings.autostart)
        self.refresh_ui()
        self.tray.show()

        if self.settings.autostart:
            self.engine.start()

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.settings.save(self.qsettings)
        self.integration.sync_autostart(settings.autostart)
        self.engine.set_settings(settings)
        self.refresh_ui()

    def notify(self, message: str, *, start: bool) -> None:
        title = "Fokus"
        icon = QSystemTrayIcon.Information
        self.tray.showMessage(title, message, icon, DEFAULT_BEEP_TIMEOUT_MS)
        if start and self.settings.timer_start_sfx_enabled:
            self.sound_manager.play(self.settings.timer_start_sfx_filepath, fallback_beep=True)
        if not start and self.settings.timer_stop_sfx_enabled:
            self.sound_manager.play(self.settings.timer_stop_sfx_filepath, fallback_beep=True)

    def refresh_ui(self) -> None:
        self.time_action.setText(self.engine.format_counter())
        self.status_action.setText(self.engine.status_text.title())
        self.primary_action.setText(self.engine.primary_action_text())
        self.secondary_action.setText(self.engine.secondary_action_text())
        self.skip_action.setVisible(not self.settings.flowmodoro_mode_enabled)
        self.postpone_action.setVisible(self.engine.is_break())
        self.tray.setIcon(available_icon(self.engine.tray_frame()))
        tooltip = self.engine.tooltip_text()
        self.tray.setToolTip(f"Fokus — {self.engine.format_counter()}" + (f" — {tooltip}" if tooltip else ""))
        self.timer_window.refresh()
        self.overlay.refresh()
        self.overlay.sync_visibility()

        if (
            self.engine.running
            and not self.engine.is_break()
            and self.settings.timer_tick_sfx_enabled
            and 0 < self.engine.counter_seconds <= self.settings.ticking_time
        ):
            volume = 1 - (self.engine.counter_seconds / max(1, self.settings.ticking_time))
            self.sound_manager.play(self.settings.timer_tick_sfx_filepath, volume=volume, fallback_beep=False)

    def show_timer_window(self) -> None:
        self.timer_window.show()
        self.timer_window.raise_()
        self.timer_window.activateWindow()

    def show_settings(self) -> None:
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def _handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            if self.timer_window.isVisible():
                self.timer_window.hide()
            else:
                self.show_timer_window()


def ensure_assets_exist() -> None:
    start_icon = icon_path("pomodoro-start-light.svg")
    if not start_icon.is_file():
        raise FileNotFoundError(f"Missing icon assets at {start_icon}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ensure_assets_exist()
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName(APP_ORG)
    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Fokus", "No system tray/menu bar is available on this system.")
        return 1
    fokus = FokusApp(app)
    return app.exec()
