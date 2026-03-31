from __future__ import annotations

import logging
import plistlib
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Property, QSettings, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QFontDatabase
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtQml import QQmlPropertyMap
from PySide6.QtWidgets import QApplication

LOGGER = logging.getLogger("fokus_macos")
APP_ORG = "com.dv"
APP_NAME = "Fokus"
LAUNCH_AGENT_ID = "com.dv.fokus.macos"
POSTPONE_MIGRATION_KEY = "portable_refactor_postpone_migration_v2"


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
        defaults = cls()
        values: dict[str, object] = {}
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
        elif self.settings.flowmodoro_mode_enabled:
            self.skip()
        else:
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
                self.scripts.run_if_enabled(self.settings.start_break_script_enabled, self.settings.start_break_script_filepath)
            else:
                self.scripts.run_if_enabled(self.settings.start_focus_script_enabled, self.settings.start_focus_script_filepath)
            return
        if phase == "end":
            if self.is_break():
                self.scripts.run_if_enabled(self.settings.end_break_script_enabled, self.settings.end_break_script_filepath)
            else:
                self.scripts.run_if_enabled(self.settings.end_focus_script_enabled, self.settings.end_focus_script_filepath)

    def _set_time(self) -> None:
        current_ms = int(time.monotonic() * 1000)
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
        self.next_state()
        self.reset_time()
        auto_continue = (self.is_break() and self.settings.timer_auto_pause_enabled) or (
            not self.is_break() and self.settings.timer_auto_focus_enabled
        )
        if auto_continue:
            self.start()
        else:
            self.updated.emit()


class FokusBackend(QObject):
    stateUpdated = Signal()
    notificationRequested = Signal(str)
    activateWindowRequested = Signal(str)

    def __init__(self, qsettings: QSettings) -> None:
        super().__init__()
        self.qsettings = qsettings
        self.settings = AppSettings.load(qsettings)
        self._migrate_saved_settings()
        self.sound_manager = SoundManager()
        self.script_runner = ScriptRunner()
        self.integration = MacOSIntegration()
        self.engine = TimerEngine(self.settings, self.script_runner, self.integration)
        self.engine.updated.connect(self.refresh_state)
        self.engine.start_notification.connect(self._handle_start_notification)
        self.engine.end_notification.connect(self._handle_end_notification)
        self.state_map = QQmlPropertyMap(self)
        self.draft_settings_map = QQmlPropertyMap(self)
        self.ui_map = QQmlPropertyMap(self)
        self._font_options = [{"text": "Default", "value": ""}] + [
            {"text": family, "value": family} for family in QFontDatabase().families()
        ]
        self._wheel_deltas: dict[str, float] = {}
        self._last_tick_second: Optional[int] = None
        self._overlay_dismissed = False
        self._last_overlay_mode = (False, False)
        self.integration.sync_autostart(self.settings.autostart)
        self._populate_draft_settings()
        self.ui_map.insert("mainWindowVisible", False)
        self.ui_map.insert("settingsWindowVisible", False)
        self.ui_map.insert("breakOverlayVisible", False)
        self.refresh_state()
        if self.settings.autostart:
            self.engine.start()

    def _migrate_saved_settings(self) -> None:
        if self.qsettings.value(POSTPONE_MIGRATION_KEY, False, type=bool):
            return
        if not self.settings.flowmodoro_mode_enabled and not self.settings.fullscreen_buttons_postpone:
            self.settings.fullscreen_buttons_postpone = True
            self.settings.save(self.qsettings)
        self.qsettings.setValue(POSTPONE_MIGRATION_KEY, True)
        self.qsettings.sync()

    @Property(QObject, constant=True)
    def state(self) -> QObject:
        return self.state_map

    @Property(QObject, constant=True)
    def draftSettings(self) -> QObject:
        return self.draft_settings_map

    @Property(QObject, constant=True)
    def ui(self) -> QObject:
        return self.ui_map

    @Property("QVariantList", constant=True)
    def fontOptions(self):
        return self._font_options

    def _populate_draft_settings(self) -> None:
        for key, value in asdict(self.settings).items():
            self.draft_settings_map.insert(key, value)

    def _draft_to_settings(self) -> AppSettings:
        defaults = AppSettings()
        values: dict[str, object] = {}
        for item in fields(AppSettings):
            raw = self.draft_settings_map.value(item.name)
            default = getattr(defaults, item.name)
            if isinstance(default, bool):
                values[item.name] = bool(raw)
            elif isinstance(default, int):
                values[item.name] = int(raw)
            else:
                values[item.name] = "" if raw is None else str(raw)
        return AppSettings(**values)

    def refresh_state(self) -> None:
        state = {
            "timeText": self.engine.format_counter(),
            "statusText": self.engine.status_text.title(),
            "statusKey": self.engine.status_text,
            "running": self.engine.running,
            "isBreak": self.engine.is_break(),
            "flowmodoroModeEnabled": self.settings.flowmodoro_mode_enabled,
            "sessionCount": self.settings.number_of_sessions,
            "pageIndex": max(0, self.engine.current_session_index() - 1),
            "sessionText": (
                f"Session {self.engine.current_session_index()} / {self.settings.number_of_sessions}"
                if not self.settings.flowmodoro_mode_enabled
                else "Flowmodoro"
            ),
            "primaryActionText": self.engine.primary_action_text(),
            "secondaryActionText": self.engine.secondary_action_text(),
            "showSkipButton": not self.settings.flowmodoro_mode_enabled,
            "showPostponeButton": self.engine.is_break(),
            "showButtonsOnHover": self.settings.show_buttons_on_hover,
            "clockFontFamily": self.settings.clock_fontfamily,
            "progressDegrees": self._progress_degrees(),
            "trayFrame": -1 if self.engine.tray_frame() is None else self.engine.tray_frame(),
            "tooltipText": self.engine.tooltip_text(),
            "showFullscreenBreak": self.settings.show_fullscreen_break,
            "fullscreenButtonsPostpone": self.settings.fullscreen_buttons_postpone,
            "fullscreenButtonsSkip": self.settings.fullscreen_buttons_skip,
            "fullscreenButtonsClose": self.settings.fullscreen_buttons_close,
        }
        for key, value in state.items():
            self.state_map.insert(key, value)

        overlay_mode = (self.engine.running, self.engine.is_break())
        if overlay_mode != self._last_overlay_mode:
            self._overlay_dismissed = False
            self._last_overlay_mode = overlay_mode
        break_visible = (
            self.settings.show_fullscreen_break
            and self.engine.is_break()
            and self.engine.running
            and not self._overlay_dismissed
        )
        self.ui_map.insert("breakOverlayVisible", break_visible)
        self._maybe_play_tick()
        self.stateUpdated.emit()
        if break_visible:
            self.activateWindowRequested.emit("break")

    def _progress_degrees(self) -> int:
        if self.settings.flowmodoro_mode_enabled and not self.engine.is_break():
            return 0
        if self.engine.initial_seconds <= 0:
            return 0
        return int(max(0, min(360, round((self.engine.counter_seconds / self.engine.initial_seconds) * 360))))

    def _maybe_play_tick(self) -> None:
        should_tick = (
            self.engine.running
            and not self.engine.is_break()
            and self.settings.timer_tick_sfx_enabled
            and 0 < self.engine.counter_seconds <= self.settings.ticking_time
        )
        if not should_tick:
            self._last_tick_second = None
            return
        if self._last_tick_second == self.engine.counter_seconds:
            return
        self._last_tick_second = self.engine.counter_seconds
        volume = 1 - (self.engine.counter_seconds / max(1, self.settings.ticking_time))
        self.sound_manager.play(self.settings.timer_tick_sfx_filepath, volume=volume)

    def _handle_start_notification(self, message: str) -> None:
        if self.settings.timer_start_sfx_enabled:
            self.sound_manager.play(self.settings.timer_start_sfx_filepath, fallback_beep=True)
        self.notificationRequested.emit(message)

    def _handle_end_notification(self, message: str) -> None:
        if self.settings.timer_stop_sfx_enabled:
            self.sound_manager.play(self.settings.timer_stop_sfx_filepath, fallback_beep=True)
        self.notificationRequested.emit(message)

    @Slot()
    def start(self) -> None:
        self.engine.start()

    @Slot()
    def pause(self) -> None:
        self.engine.pause()

    @Slot()
    def activatePrimary(self) -> None:
        self.engine.activate_primary()

    @Slot()
    def stop(self) -> None:
        self.engine.stop()

    @Slot()
    def skip(self) -> None:
        self.engine.skip()

    @Slot()
    def postpone(self) -> None:
        self.engine.postpone()

    def adjust_timer_by_wheel_delta(
        self,
        source_key: str,
        event_delta: float,
        *,
        step_threshold: float = 120.0,
    ) -> float:
        wheel_delta = self._wheel_deltas.get(source_key, 0.0)
        if self.settings.flowmodoro_mode_enabled or event_delta == 0:
            return wheel_delta
        wheel_delta += event_delta
        increment = 0
        while wheel_delta >= step_threshold:
            wheel_delta -= step_threshold
            increment += 1
        while wheel_delta <= -step_threshold:
            wheel_delta += step_threshold
            increment -= 1
        while increment != 0:
            self.engine.shift_counter(60 if increment > 0 else -60)
            increment += -1 if increment > 0 else 1
        self._wheel_deltas[source_key] = wheel_delta
        return wheel_delta

    @Slot(int)
    def adjustTimerByWheel(self, event_delta: int) -> None:
        self.adjust_timer_by_wheel_delta("window", float(event_delta))

    @Slot()
    def toggleMainWindow(self) -> None:
        visible = bool(self.ui_map.value("mainWindowVisible"))
        self.ui_map.insert("mainWindowVisible", not visible)
        if not visible:
            self.activateWindowRequested.emit("timer")

    @Slot()
    def showMainWindow(self) -> None:
        self.ui_map.insert("mainWindowVisible", True)
        self.activateWindowRequested.emit("timer")

    @Slot()
    def hideMainWindow(self) -> None:
        self.ui_map.insert("mainWindowVisible", False)

    @Slot()
    def openSettings(self) -> None:
        self._populate_draft_settings()
        self.ui_map.insert("settingsWindowVisible", True)
        self.activateWindowRequested.emit("settings")

    @Slot()
    def closeSettings(self) -> None:
        self.ui_map.insert("settingsWindowVisible", False)
        self._populate_draft_settings()

    @Slot()
    def saveSettings(self) -> None:
        settings = self._draft_to_settings()
        if settings.flowmodoro_mode_enabled:
            settings.fullscreen_buttons_postpone = False
        elif self.settings.flowmodoro_mode_enabled and not settings.flowmodoro_mode_enabled:
            settings.fullscreen_buttons_postpone = True
        self.settings = settings
        self.settings.save(self.qsettings)
        self.integration.sync_autostart(self.settings.autostart)
        self.engine.set_settings(self.settings)
        self._populate_draft_settings()
        self.ui_map.insert("settingsWindowVisible", False)
        self.refresh_state()

    @Slot(str)
    def previewSound(self, path: str) -> None:
        self.sound_manager.preview(path)

    @Slot(str, result=str)
    def toLocalPath(self, value: str) -> str:
        if value.startswith("file://"):
            return QUrl(value).toLocalFile()
        return value

    @Slot()
    def closeBreakOverlay(self) -> None:
        self._overlay_dismissed = True
        self.ui_map.insert("breakOverlayVisible", False)
