import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"

Window {
    id: timerWindow
    width: 420
    height: 360
    minimumWidth: 360
    minimumHeight: 280
    visible: AppUi.mainWindowVisible
    title: "Fokus"

    color: palette.window

    onClosing: function(close) {
        close.accepted = false
        Backend.hideMainWindow()
    }

    onVisibleChanged: {
        if (visible) {
            raise()
            requestActivate()
        }
    }

    Connections {
        target: Backend
        function onActivateWindowRequested(name) {
            if (name === "timer" && timerWindow.visible) {
                timerWindow.raise()
                timerWindow.requestActivate()
            }
        }
    }

    Item {
        anchors.fill: parent

        MouseArea {
            anchors.fill: parent
            onWheel: function(wheel) {
                Backend.adjustTimerByWheel(wheel.angleDelta.y)
                wheel.accepted = true
            }
        }

        HoverHandler {
            id: hover
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 14

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: AppState.sessionText
                color: palette.mid
                font.pointSize: 11
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TimerFace {
                    anchors.fill: parent
                    timeText: AppState.timeText
                    statusText: AppState.statusText
                    progressDegrees: AppState.progressDegrees
                    isBreak: AppState.isBreak
                    clockFontFamily: AppState.clockFontFamily
                    showPageIndicator: !AppState.flowmodoroModeEnabled
                    sessionCount: AppState.sessionCount
                    pageIndex: AppState.pageIndex
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                visible: !AppState.showButtonsOnHover || hover.hovered

                Button {
                    text: "Skip"
                    visible: AppState.showSkipButton
                    onClicked: Backend.skip()
                }

                Button {
                    text: AppState.primaryActionText
                    onClicked: Backend.activatePrimary()
                }

                Button {
                    text: AppState.secondaryActionText
                    onClicked: Backend.stop()
                }
            }
        }
    }
}
