import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ColumnLayout {
        width: parent.width
        spacing: 16

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 16
            rowSpacing: 12

            Label { text: qsTr("Number of sessions") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.number_of_sessions; from: 1; to: 10; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onValueModified: AppDraftSettings.number_of_sessions = value }
            Label { text: qsTr("Focus minutes") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.focus_time; from: 1; to: 9999; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onValueModified: AppDraftSettings.focus_time = value }
            Label { text: qsTr("Short break minutes") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.short_break_time; from: 0; to: 9999; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onValueModified: AppDraftSettings.short_break_time = value }
            Label { text: qsTr("Long break minutes") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.long_break_time; from: 0; to: 9999; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onValueModified: AppDraftSettings.long_break_time = value }
            Label { text: qsTr("Ticking time (seconds)") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.ticking_time; from: 0; to: 60; onValueModified: AppDraftSettings.ticking_time = value }
            Label { text: qsTr("Flow divisor") }
            SpinBox { Layout.fillWidth: true; value: AppDraftSettings.flow_divisor; from: 1; to: 9999; enabled: AppDraftSettings.flowmodoro_mode_enabled; onValueModified: AppDraftSettings.flow_divisor = value }
        }
    }
}
