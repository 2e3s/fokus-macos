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
        anchors.margins: 16
        spacing: 12

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { text: qsTr("General") }
            TabButton { text: qsTr("Timer") }
            TabButton { text: qsTr("Notifications") }
            TabButton { text: qsTr("Scripts") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex
            GeneralPage {}
            TimerPage {}
            NotificationsPage {}
            ScriptsPage {}
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 12
            Button { text: qsTr("Cancel"); onClicked: Backend.closeSettings() }
            Button { text: qsTr("Save"); onClicked: Backend.saveSettings() }
        }
    }
}
