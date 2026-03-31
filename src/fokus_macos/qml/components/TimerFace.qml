import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property string timeText: "25:00"
    property string statusText: "Focus"
    property int progressDegrees: 360
    property bool isBreak: false
    property string clockFontFamily: ""
    property bool showPageIndicator: true
    property int sessionCount: 4
    property int pageIndex: 0
    property bool compact: false

    readonly property color accentColor: isBreak ? palette.mid : palette.highlight
    readonly property color textColor: palette.windowText

    ProgressCircle {
        id: progressCircle
        anchors.centerIn: parent
        size: compact ? Math.min(parent.width / 1.8, parent.height / 1.8) : Math.min(parent.width / 1.4, parent.height / 1.4)
        colorCircle: root.accentColor
        arcBegin: 0
        arcEnd: root.progressDegrees
        lineWidth: size / 30
    }

    Item {
        anchors.centerIn: parent
        height: timeLabel.height
        width: Math.max(timeLabel.width, pageIndicator.implicitWidth)

        PageIndicator {
            id: pageIndicator
            visible: root.showPageIndicator && root.sessionCount > 1
            count: root.sessionCount
            currentIndex: root.pageIndex
            spacing: progressCircle.width / 25
            anchors.bottom: timeLabel.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: progressCircle.width / 15
        }

        Label {
            id: timeLabel
            text: root.timeText
            font.pointSize: Math.max(progressCircle.width / 8, 1)
            font.family: root.clockFontFamily
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
        }

        Label {
            text: root.statusText
            font.pointSize: Math.max(progressCircle.width / 24, 1)
            color: root.isBreak ? palette.mid : palette.windowText
            anchors.top: timeLabel.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: progressCircle.width / 20
        }
    }
}
