import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"

Window {
    id: breakWindow
    visible: AppUi.breakOverlayVisible
        flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
    title: "Break"
    color: "#DD141414"

    onVisibleChanged: {
        if (visible) {
            showFullScreen()
            raise()
            requestActivate()
        }
    }

    Connections {
        target: Backend
        function onActivateWindowRequested(name) {
            if (name === "break" && breakWindow.visible) {
                breakWindow.raise()
                breakWindow.requestActivate()
            }
        }
    }

    Item {
        anchors.fill: parent
        anchors.margins: 48

        HoverHandler {
            id: hover
        }

        TimerFace {
            anchors.fill: parent
            compact: true
            timeText: AppState.timeText
            statusText: AppState.statusText
            progressDegrees: AppState.progressDegrees
            isBreak: AppState.isBreak
            clockFontFamily: AppState.clockFontFamily
            showPageIndicator: !AppState.flowmodoroModeEnabled
            sessionCount: AppState.sessionCount
            pageIndex: AppState.pageIndex
        }

        RowLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            spacing: 12
            visible: !AppState.showButtonsOnHover || hover.hovered

            Button {
                text: "Postpone"
                visible: AppState.isBreak && AppState.fullscreenButtonsPostpone
                onClicked: Backend.postpone()
            }

            Button {
                text: "Skip"
                visible: AppState.isBreak && AppState.fullscreenButtonsSkip
                onClicked: Backend.skip()
            }

            Button {
                text: "Close"
                visible: AppState.isBreak && AppState.fullscreenButtonsClose
                onClicked: Backend.closeBreakOverlay()
            }

            Button {
                text: "Start"
                visible: !AppState.isBreak
                onClicked: Backend.start()
            }
        }
    }
}
