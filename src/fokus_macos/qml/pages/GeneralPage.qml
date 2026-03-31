import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    clip: true

    ColumnLayout {
        width: parent.width
        spacing: 16

        GroupBox {
            title: qsTr("General")
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                TextField {
                    Layout.fillWidth: true
                    placeholderText: qsTr("Clock font family (leave empty for default)")
                    text: AppDraftSettings.clock_fontfamily
                    onTextChanged: AppDraftSettings.clock_fontfamily = text
                }
                CheckBox { text: qsTr("Show icon in menu bar"); checked: AppDraftSettings.show_icon_in_compact_mode; onToggled: AppDraftSettings.show_icon_in_compact_mode = checked }
                CheckBox { text: qsTr("Show time in menu bar"); checked: AppDraftSettings.show_time_in_compact_mode; onToggled: AppDraftSettings.show_time_in_compact_mode = checked }
                CheckBox { text: qsTr("Launch at login"); checked: AppDraftSettings.autostart; onToggled: AppDraftSettings.autostart = checked }
                CheckBox { text: qsTr("Enable Do Not Disturb during focus"); checked: AppDraftSettings.do_not_disturb_enabled; onToggled: AppDraftSettings.do_not_disturb_enabled = checked }
                CheckBox { text: qsTr("Auto-start focus sessions"); checked: AppDraftSettings.timer_auto_focus_enabled; onToggled: AppDraftSettings.timer_auto_focus_enabled = checked }
                CheckBox { text: qsTr("Auto-start break sessions"); checked: AppDraftSettings.timer_auto_pause_enabled; onToggled: AppDraftSettings.timer_auto_pause_enabled = checked }
                CheckBox { text: qsTr("Show fullscreen break overlay"); checked: AppDraftSettings.show_fullscreen_break; onToggled: AppDraftSettings.show_fullscreen_break = checked }
                CheckBox { text: qsTr("Overlay shows Postpone"); checked: AppDraftSettings.fullscreen_buttons_postpone; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onToggled: AppDraftSettings.fullscreen_buttons_postpone = checked }
                CheckBox { text: qsTr("Overlay shows Skip"); checked: AppDraftSettings.fullscreen_buttons_skip; onToggled: AppDraftSettings.fullscreen_buttons_skip = checked }
                CheckBox { text: qsTr("Overlay shows Close"); checked: AppDraftSettings.fullscreen_buttons_close; onToggled: AppDraftSettings.fullscreen_buttons_close = checked }
                CheckBox { text: qsTr("Show buttons only on hover"); checked: AppDraftSettings.show_buttons_on_hover; onToggled: AppDraftSettings.show_buttons_on_hover = checked }
                CheckBox {
                    text: qsTr("Enable Flowmodoro mode")
                    checked: AppDraftSettings.flowmodoro_mode_enabled
                    onToggled: {
                        AppDraftSettings.flowmodoro_mode_enabled = checked
                        if (checked)
                            AppDraftSettings.fullscreen_buttons_postpone = false
                    }
                }
            }
        }
    }
}
