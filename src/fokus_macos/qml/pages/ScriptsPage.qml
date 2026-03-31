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
        spacing: 12

        GridLayout {
            Layout.fillWidth: true
            columns: 4
            columnSpacing: 12
            rowSpacing: 10

            Label { text: qsTr("Start focus") }
            CheckBox { text: qsTr("Enabled"); checked: AppDraftSettings.start_focus_script_enabled; onToggled: AppDraftSettings.start_focus_script_enabled = checked }
            TextField { Layout.fillWidth: true; text: AppDraftSettings.start_focus_script_filepath; enabled: AppDraftSettings.start_focus_script_enabled; onTextChanged: AppDraftSettings.start_focus_script_filepath = text }
            Button { text: qsTr("Choose"); enabled: AppDraftSettings.start_focus_script_enabled; onClicked: startFocusDialog.open() }

            Label { text: qsTr("Start break") }
            CheckBox { text: qsTr("Enabled"); checked: AppDraftSettings.start_break_script_enabled; onToggled: AppDraftSettings.start_break_script_enabled = checked }
            TextField { Layout.fillWidth: true; text: AppDraftSettings.start_break_script_filepath; enabled: AppDraftSettings.start_break_script_enabled; onTextChanged: AppDraftSettings.start_break_script_filepath = text }
            Button { text: qsTr("Choose"); enabled: AppDraftSettings.start_break_script_enabled; onClicked: startBreakDialog.open() }

            Label { text: qsTr("End focus") }
            CheckBox { text: qsTr("Enabled"); checked: AppDraftSettings.end_focus_script_enabled; onToggled: AppDraftSettings.end_focus_script_enabled = checked }
            TextField { Layout.fillWidth: true; text: AppDraftSettings.end_focus_script_filepath; enabled: AppDraftSettings.end_focus_script_enabled; onTextChanged: AppDraftSettings.end_focus_script_filepath = text }
            Button { text: qsTr("Choose"); enabled: AppDraftSettings.end_focus_script_enabled; onClicked: endFocusDialog.open() }

            Label { text: qsTr("End break") }
            CheckBox { text: qsTr("Enabled"); checked: AppDraftSettings.end_break_script_enabled; onToggled: AppDraftSettings.end_break_script_enabled = checked }
            TextField { Layout.fillWidth: true; text: AppDraftSettings.end_break_script_filepath; enabled: AppDraftSettings.end_break_script_enabled; onTextChanged: AppDraftSettings.end_break_script_filepath = text }
            Button { text: qsTr("Choose"); enabled: AppDraftSettings.end_break_script_enabled; onClicked: endBreakDialog.open() }

            Label { text: qsTr("Stop/reset") }
            CheckBox { text: qsTr("Enabled"); checked: AppDraftSettings.stop_script_enabled; onToggled: AppDraftSettings.stop_script_enabled = checked }
            TextField { Layout.fillWidth: true; text: AppDraftSettings.stop_script_filepath; enabled: AppDraftSettings.stop_script_enabled; onTextChanged: AppDraftSettings.stop_script_filepath = text }
            Button { text: qsTr("Choose"); enabled: AppDraftSettings.stop_script_enabled; onClicked: stopDialog.open() }
        }
    }

    FileDialog { id: startFocusDialog; nameFilters: [qsTr("Script file (*.sh)"), qsTr("All files (*)")]; onAccepted: root.bindFile("start_focus_script_filepath", startFocusDialog) }
    FileDialog { id: startBreakDialog; nameFilters: [qsTr("Script file (*.sh)"), qsTr("All files (*)")]; onAccepted: root.bindFile("start_break_script_filepath", startBreakDialog) }
    FileDialog { id: endFocusDialog; nameFilters: [qsTr("Script file (*.sh)"), qsTr("All files (*)")]; onAccepted: root.bindFile("end_focus_script_filepath", endFocusDialog) }
    FileDialog { id: endBreakDialog; nameFilters: [qsTr("Script file (*.sh)"), qsTr("All files (*)")]; onAccepted: root.bindFile("end_break_script_filepath", endBreakDialog) }
    FileDialog { id: stopDialog; nameFilters: [qsTr("Script file (*.sh)"), qsTr("All files (*)")]; onAccepted: root.bindFile("stop_script_filepath", stopDialog) }
}
