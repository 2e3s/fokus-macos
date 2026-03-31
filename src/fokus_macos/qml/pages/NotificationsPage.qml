import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ScrollView {
    id: root
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    function bindFile(targetKey, dialog) {
        AppDraftSettings[targetKey] = Backend.toLocalPath(dialog.selectedFile.toString())
    }

    ColumnLayout {
        width: parent.width
        spacing: 16

        GroupBox {
            title: qsTr("Start")
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                CheckBox { text: qsTr("Show notification"); checked: AppDraftSettings.timer_start_notification_enabled; onToggled: AppDraftSettings.timer_start_notification_enabled = checked }
                CheckBox { text: qsTr("Play sound"); checked: AppDraftSettings.timer_start_sfx_enabled; onToggled: AppDraftSettings.timer_start_sfx_enabled = checked }
                RowLayout {
                    TextField { Layout.fillWidth: true; text: AppDraftSettings.timer_start_sfx_filepath; enabled: AppDraftSettings.timer_start_sfx_enabled; onTextChanged: AppDraftSettings.timer_start_sfx_filepath = text }
                    Button { text: qsTr("Choose"); enabled: AppDraftSettings.timer_start_sfx_enabled; onClicked: startDialog.open() }
                    Button { text: qsTr("Preview"); enabled: AppDraftSettings.timer_start_sfx_enabled; onClicked: Backend.previewSound(AppDraftSettings.timer_start_sfx_filepath) }
                }
            }
        }

        GroupBox {
            title: qsTr("End")
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                CheckBox { text: qsTr("Show notification"); checked: AppDraftSettings.timer_end_notification_enabled; onToggled: AppDraftSettings.timer_end_notification_enabled = checked }
                CheckBox { text: qsTr("Play sound"); checked: AppDraftSettings.timer_stop_sfx_enabled; onToggled: AppDraftSettings.timer_stop_sfx_enabled = checked }
                RowLayout {
                    TextField { Layout.fillWidth: true; text: AppDraftSettings.timer_stop_sfx_filepath; enabled: AppDraftSettings.timer_stop_sfx_enabled; onTextChanged: AppDraftSettings.timer_stop_sfx_filepath = text }
                    Button { text: qsTr("Choose"); enabled: AppDraftSettings.timer_stop_sfx_enabled; onClicked: stopDialog.open() }
                    Button { text: qsTr("Preview"); enabled: AppDraftSettings.timer_stop_sfx_enabled; onClicked: Backend.previewSound(AppDraftSettings.timer_stop_sfx_filepath) }
                }
            }
        }

        GroupBox {
            title: qsTr("Tick")
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                CheckBox { text: qsTr("Play ticking sound"); checked: AppDraftSettings.timer_tick_sfx_enabled; onToggled: AppDraftSettings.timer_tick_sfx_enabled = checked }
                RowLayout {
                    TextField { Layout.fillWidth: true; text: AppDraftSettings.timer_tick_sfx_filepath; enabled: AppDraftSettings.timer_tick_sfx_enabled; onTextChanged: AppDraftSettings.timer_tick_sfx_filepath = text }
                    Button { text: qsTr("Choose"); enabled: AppDraftSettings.timer_tick_sfx_enabled; onClicked: tickDialog.open() }
                    Button { text: qsTr("Preview"); enabled: AppDraftSettings.timer_tick_sfx_enabled; onClicked: Backend.previewSound(AppDraftSettings.timer_tick_sfx_filepath) }
                }
            }
        }
    }

    FileDialog { id: startDialog; nameFilters: [qsTr("Sound files (*.wav *.mp3 *.oga *.ogg *.m4a *.aiff)"), qsTr("All files (*)")]; onAccepted: root.bindFile("timer_start_sfx_filepath", startDialog) }
    FileDialog { id: stopDialog; nameFilters: [qsTr("Sound files (*.wav *.mp3 *.oga *.ogg *.m4a *.aiff)"), qsTr("All files (*)")]; onAccepted: root.bindFile("timer_stop_sfx_filepath", stopDialog) }
    FileDialog { id: tickDialog; nameFilters: [qsTr("Sound files (*.wav *.mp3 *.oga *.ogg *.m4a *.aiff)"), qsTr("All files (*)")]; onAccepted: root.bindFile("timer_tick_sfx_filepath", tickDialog) }
}
