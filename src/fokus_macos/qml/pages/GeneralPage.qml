import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ListModel {
        id: fontModel
    }

    Component.onCompleted: {
        fontModel.clear()
        for (var i = 0; i < Backend.fontOptions.length; ++i)
            fontModel.append(Backend.fontOptions[i])
        syncFontSelection()
    }

    function syncFontSelection() {
        var currentValue = AppDraftSettings.clock_fontfamily
        fontBox.currentIndex = 0
        for (var i = 0; i < fontModel.count; ++i) {
            if (fontModel.get(i).value === currentValue) {
                fontBox.currentIndex = i
                break
            }
        }
    }

    ColumnLayout {
        width: parent.width
        spacing: 16

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 16
            rowSpacing: 12

            Label { text: qsTr("Timer font") }
            ComboBox {
                id: fontBox
                Layout.fillWidth: true
                model: fontModel
                textRole: "text"
                valueRole: "value"
                onActivated: AppDraftSettings.clock_fontfamily = currentValue
            }

            Label { text: qsTr("Compact view") }
            RowLayout {
                CheckBox { text: qsTr("Show icon"); checked: AppDraftSettings.show_icon_in_compact_mode; onToggled: AppDraftSettings.show_icon_in_compact_mode = checked }
                CheckBox { text: qsTr("Show time"); checked: AppDraftSettings.show_time_in_compact_mode; onToggled: AppDraftSettings.show_time_in_compact_mode = checked }
            }

            Label { text: qsTr("System") }
            ColumnLayout {
                CheckBox { text: qsTr("Launch at login"); checked: AppDraftSettings.autostart; onToggled: AppDraftSettings.autostart = checked }
                CheckBox { text: qsTr("Enable Do Not Disturb during focus"); checked: AppDraftSettings.do_not_disturb_enabled; onToggled: AppDraftSettings.do_not_disturb_enabled = checked }
            }

            Label { text: qsTr("Auto-start timer for") }
            RowLayout {
                CheckBox { text: qsTr("Focus"); checked: AppDraftSettings.timer_auto_focus_enabled; onToggled: AppDraftSettings.timer_auto_focus_enabled = checked }
                CheckBox { text: qsTr("Break"); checked: AppDraftSettings.timer_auto_pause_enabled; onToggled: AppDraftSettings.timer_auto_pause_enabled = checked }
            }

            Label { text: qsTr("Break overlay") }
            ColumnLayout {
                CheckBox { text: qsTr("Show fullscreen overlay"); checked: AppDraftSettings.show_fullscreen_break; onToggled: AppDraftSettings.show_fullscreen_break = checked }
                RowLayout {
                    CheckBox { text: qsTr("Postpone"); checked: AppDraftSettings.fullscreen_buttons_postpone; enabled: !AppDraftSettings.flowmodoro_mode_enabled; onToggled: AppDraftSettings.fullscreen_buttons_postpone = checked }
                    CheckBox { text: qsTr("Skip"); checked: AppDraftSettings.fullscreen_buttons_skip; onToggled: AppDraftSettings.fullscreen_buttons_skip = checked }
                    CheckBox { text: qsTr("Close"); checked: AppDraftSettings.fullscreen_buttons_close; onToggled: AppDraftSettings.fullscreen_buttons_close = checked }
                }
                CheckBox { text: qsTr("Show buttons only on hover"); checked: AppDraftSettings.show_buttons_on_hover; onToggled: AppDraftSettings.show_buttons_on_hover = checked }
            }

            Label { text: qsTr("Mode") }
            CheckBox {
                text: qsTr("Enable Flowmodoro mode")
                checked: AppDraftSettings.flowmodoro_mode_enabled
                onToggled: {
                    AppDraftSettings.flowmodoro_mode_enabled = checked
                    AppDraftSettings.fullscreen_buttons_postpone = !checked
                }
            }
        }
    }
}
