import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "pages"

Window {
    id: settingsWindow
    width: 760
    height: 680
    minimumWidth: 640
    minimumHeight: 560
    visible: AppUi.settingsWindowVisible
    title: "Fokus Settings"
    color: palette.window

    onClosing: function(close) {
        close.accepted = false
        Backend.closeSettings()
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
            if (name === "settings" && settingsWindow.visible) {
                settingsWindow.raise()
                settingsWindow.requestActivate()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        Label {
            Layout.fillWidth: true
            text: qsTr("Settings")
            font.pixelSize: 24
            font.weight: Font.DemiBold
        }

        TabBar {
            id: tabs
            Layout.fillWidth: true
            spacing: 8
            background: Rectangle {
                radius: 12
                color: Qt.rgba(
                    settingsWindow.palette.window.r,
                    settingsWindow.palette.window.g,
                    settingsWindow.palette.window.b,
                    0.55
                )
                border.width: 1
                border.color: Qt.rgba(
                    settingsWindow.palette.mid.r,
                    settingsWindow.palette.mid.g,
                    settingsWindow.palette.mid.b,
                    0.25
                )
            }

            TabButton {
                id: generalTab
                text: qsTr("General")
                implicitHeight: 36
                leftPadding: 16
                rightPadding: 16
                contentItem: Text {
                    text: generalTab.text
                    color: generalTab.checked ? settingsWindow.palette.buttonText : Qt.rgba(1, 1, 1, 0.7)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 10
                    color: generalTab.checked ? settingsWindow.palette.base : "transparent"
                    border.width: generalTab.checked ? 1 : 0
                    border.color: Qt.rgba(
                        settingsWindow.palette.mid.r,
                        settingsWindow.palette.mid.g,
                        settingsWindow.palette.mid.b,
                        0.25
                    )
                }
            }
            TabButton {
                id: timerTab
                text: qsTr("Timer")
                implicitHeight: 36
                leftPadding: 16
                rightPadding: 16
                contentItem: Text {
                    text: timerTab.text
                    color: timerTab.checked ? settingsWindow.palette.buttonText : Qt.rgba(1, 1, 1, 0.7)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 10
                    color: timerTab.checked ? settingsWindow.palette.base : "transparent"
                    border.width: timerTab.checked ? 1 : 0
                    border.color: Qt.rgba(
                        settingsWindow.palette.mid.r,
                        settingsWindow.palette.mid.g,
                        settingsWindow.palette.mid.b,
                        0.25
                    )
                }
            }
            TabButton {
                id: notificationsTab
                text: qsTr("Notifications")
                implicitHeight: 36
                leftPadding: 16
                rightPadding: 16
                contentItem: Text {
                    text: notificationsTab.text
                    color: notificationsTab.checked ? settingsWindow.palette.buttonText : Qt.rgba(1, 1, 1, 0.7)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 10
                    color: notificationsTab.checked ? settingsWindow.palette.base : "transparent"
                    border.width: notificationsTab.checked ? 1 : 0
                    border.color: Qt.rgba(
                        settingsWindow.palette.mid.r,
                        settingsWindow.palette.mid.g,
                        settingsWindow.palette.mid.b,
                        0.25
                    )
                }
            }
            TabButton {
                id: scriptsTab
                text: qsTr("Scripts")
                implicitHeight: 36
                leftPadding: 16
                rightPadding: 16
                contentItem: Text {
                    text: scriptsTab.text
                    color: scriptsTab.checked ? settingsWindow.palette.buttonText : Qt.rgba(1, 1, 1, 0.7)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 10
                    color: scriptsTab.checked ? settingsWindow.palette.base : "transparent"
                    border.width: scriptsTab.checked ? 1 : 0
                    border.color: Qt.rgba(
                        settingsWindow.palette.mid.r,
                        settingsWindow.palette.mid.g,
                        settingsWindow.palette.mid.b,
                        0.25
                    )
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            StackLayout {
                anchors.fill: parent
                currentIndex: tabs.currentIndex
                GeneralPage {}
                TimerPage {}
                NotificationsPage {}
                ScriptsPage {}
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 12
            Button { text: qsTr("Cancel"); onClicked: Backend.closeSettings() }
            Button { text: qsTr("Save"); onClicked: Backend.saveSettings() }
        }
    }
}
