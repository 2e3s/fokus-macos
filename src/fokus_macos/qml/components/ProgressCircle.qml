import QtQuick
import QtQuick.Shapes

Item {
    id: root

    property int size: 200
    property real arcBegin: 0
    property real arcEnd: 270
    property real arcOffset: 0
    property bool isPie: false
    property bool showBackground: false
    property real lineWidth: 20
    property color colorCircle: "#CC3333"
    property color colorBackground: "#779933"
    property alias beginAnimation: animationArcBegin.enabled
    property alias endAnimation: animationArcEnd.enabled
    property int animationDuration: 200

    width: size
    height: size
    readonly property real radius: (width / 2) - lineWidth / 2
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2
    readonly property real startRadians: (arcBegin - 90 + arcOffset) * Math.PI / 180
    readonly property real startX: centerX + Math.cos(startRadians) * radius
    readonly property real startY: centerY + Math.sin(startRadians) * radius
    readonly property real sweepAngle: arcEnd - arcBegin

    Shape {
        anchors.fill: parent

        ShapePath {
            fillColor: "transparent"
            strokeColor: root.showBackground ? root.colorBackground : "transparent"
            strokeWidth: root.showBackground ? root.lineWidth : 0
            capStyle: ShapePath.RoundCap
            startX: root.centerX + root.radius
            startY: root.centerY
            PathAngleArc {
                centerX: root.centerX
                centerY: root.centerY
                radiusX: root.radius
                radiusY: root.radius
                startAngle: 0
                sweepAngle: 360
            }
        }

        ShapePath {
            fillColor: "transparent"
            strokeColor: root.colorCircle
            strokeWidth: root.lineWidth
            capStyle: ShapePath.RoundCap
            startX: root.startX
            startY: root.startY
            PathAngleArc {
                centerX: root.centerX
                centerY: root.centerY
                radiusX: root.radius
                radiusY: root.radius
                startAngle: root.arcBegin - 90 + root.arcOffset
                sweepAngle: root.sweepAngle
            }
        }
    }

    Behavior on arcBegin {
        id: animationArcBegin
        enabled: true
        NumberAnimation {
            duration: root.animationDuration
            easing.type: Easing.InOutCubic
        }
    }

    Behavior on arcEnd {
        id: animationArcEnd
        enabled: true
        NumberAnimation {
            duration: root.animationDuration
            easing.type: Easing.InOutCubic
        }
    }
}
