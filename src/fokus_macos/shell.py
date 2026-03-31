from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QAction, QCursor, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .backend import APP_NAME, FokusBackend
from .resources import icon_directory

try:
    from AppKit import NSEvent, NSEventMaskScrollWheel
except ImportError:  # pragma: no cover
    NSEvent = None
    NSEventMaskScrollWheel = None


def icon_path(name: str) -> Path:
    return icon_directory() / name


def available_icon(frame: Optional[int]) -> QIcon:
    if frame is None:
        return QIcon(str(icon_path("pomodoro-start-light.svg")))
    return QIcon(str(icon_path(f"pomodoro-indicator-light-{frame:02d}.svg")))


class TrayIcon(QSystemTrayIcon):
    def __init__(self, backend: FokusBackend) -> None:
        super().__init__(backend)
        self.backend = backend

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            event_delta = event.angleDelta().y() or event.pixelDelta().y()
            self.backend.adjust_timer_by_wheel_delta("tray-qt", float(event_delta))
            if event_delta != 0 and not self.backend.settings.flowmodoro_mode_enabled:
                event.accept()
                return True
        return super().event(event)


class MacOSTrayScrollMonitor(QObject):
    PRECISE_SCROLL_STEP = 6.0
    LINE_SCROLL_STEP = 1.0

    def __init__(self, tray: TrayIcon, backend: FokusBackend) -> None:
        super().__init__(backend)
        self.tray = tray
        self.backend = backend
        self.global_monitor = None
        self.local_monitor = None
        self.last_event_signature = None

        if NSEvent is None or NSEventMaskScrollWheel is None:
            return

        self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskScrollWheel,
            self.handle_global_scroll,
        )
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskScrollWheel,
            self.handle_local_scroll,
        )

    def stop(self) -> None:
        if self.global_monitor is not None and NSEvent is not None:
            NSEvent.removeMonitor_(self.global_monitor)
            self.global_monitor = None
        if self.local_monitor is not None and NSEvent is not None:
            NSEvent.removeMonitor_(self.local_monitor)
            self.local_monitor = None

    def handle_global_scroll(self, event) -> None:
        self.process_scroll(event)

    def handle_local_scroll(self, event):
        if self.process_scroll(event):
            return None
        return event

    def process_scroll(self, event) -> bool:
        geometry = self.tray.geometry()
        if geometry.isNull() or not geometry.contains(QCursor.pos()):
            return False
        if self.is_momentum_scroll(event):
            return False

        event_delta, threshold, source = self.normalize_event_delta(event)
        signature = self.event_signature(event, event_delta)
        if signature is not None and signature == self.last_event_signature:
            return False
        self.last_event_signature = signature
        self.backend.adjust_timer_by_wheel_delta(source, event_delta, step_threshold=threshold)
        return event_delta != 0 and not self.backend.settings.flowmodoro_mode_enabled

    @staticmethod
    def is_momentum_scroll(event) -> bool:
        return hasattr(event, "momentumPhase") and int(event.momentumPhase()) != 0

    @classmethod
    def normalize_event_delta(cls, event):
        if hasattr(event, "hasPreciseScrollingDeltas") and event.hasPreciseScrollingDeltas():
            return float(event.scrollingDeltaY()), cls.PRECISE_SCROLL_STEP, "tray-precise"
        delta = float(event.deltaY())
        if delta > 0:
            return 1.0, cls.LINE_SCROLL_STEP, "tray-line"
        if delta < 0:
            return -1.0, cls.LINE_SCROLL_STEP, "tray-line"
        return 0.0, cls.LINE_SCROLL_STEP, "tray-line"

    @staticmethod
    def event_signature(event, normalized_delta: float):
        if not hasattr(event, "timestamp"):
            return None
        return int(round(float(event.timestamp()) * 1000)), normalized_delta


class MacOSTrayShell(QObject):
    def __init__(self, backend: FokusBackend, app) -> None:
        super().__init__(backend)
        self.backend = backend
        self.app = app
        self.tray = TrayIcon(backend)
        self.tray.setToolTip(APP_NAME)
        self.tray.activated.connect(self._handle_tray_activation)
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)
        self.scroll_monitor = MacOSTrayScrollMonitor(self.tray, backend)
        self.app.aboutToQuit.connect(self.scroll_monitor.stop)
        self.backend.stateUpdated.connect(self.refresh)
        self.backend.notificationRequested.connect(self.notify)

        self.time_action = QAction("", self.menu)
        self.time_action.setEnabled(False)
        self.status_action = QAction("", self.menu)
        self.status_action.setEnabled(False)
        self.primary_action = QAction(self.menu)
        self.primary_action.triggered.connect(self.backend.activatePrimary)
        self.skip_action = QAction("Skip", self.menu)
        self.skip_action.triggered.connect(self.backend.skip)
        self.postpone_action = QAction("Postpone", self.menu)
        self.postpone_action.triggered.connect(self.backend.postpone)
        self.secondary_action = QAction(self.menu)
        self.secondary_action.triggered.connect(self.backend.stop)
        self.open_action = QAction("Open Timer Window", self.menu)
        self.open_action.triggered.connect(self.backend.showMainWindow)
        self.settings_action = QAction("Settings…", self.menu)
        self.settings_action.triggered.connect(self.backend.openSettings)
        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(self.app.quit)

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

        self.refresh()
        self.tray.show()

    def refresh(self) -> None:
        state = self.backend.state_map
        self.time_action.setText(str(state.value("timeText")))
        self.status_action.setText(str(state.value("statusText")))
        self.primary_action.setText(str(state.value("primaryActionText")))
        self.secondary_action.setText(str(state.value("secondaryActionText")))
        self.skip_action.setVisible(bool(state.value("showSkipButton")))
        self.postpone_action.setVisible(bool(state.value("showPostponeButton")))
        tray_frame = state.value("trayFrame")
        frame = None if tray_frame in (-1, None) else int(tray_frame)
        self.tray.setIcon(available_icon(frame))
        tooltip = str(state.value("tooltipText"))
        time_text = str(state.value("timeText"))
        self.tray.setToolTip(f"{APP_NAME} — {time_text}" + (f" — {tooltip}" if tooltip else ""))

    def notify(self, message: str) -> None:
        self.tray.showMessage(APP_NAME, message, QSystemTrayIcon.Information, 6000)

    def _handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.backend.toggleMainWindow()
