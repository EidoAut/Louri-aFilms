import QtQuick
import QtQuick.Controls
import ".."
BusyIndicator {
    id: control
    implicitWidth: 38; implicitHeight: 38
    contentItem: Item {
        Rectangle { anchors.centerIn: parent; width: 24; height: 24; radius: 12; color: Theme.transparent; border.color: Theme.border; border.width: 3 }
        Item {
            anchors.fill: parent
            Rectangle { width: 7; height: 7; radius: 4; color: Theme.red; anchors.horizontalCenter: parent.horizontalCenter; y: 3 }
            RotationAnimator on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: control.running }
        }
    }
}
