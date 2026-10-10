import QtQuick
import QtQuick.Controls.Basic as Basic
import ".."
Basic.CheckBox {
    id: control
    font.family: Theme.font; font.pixelSize: Theme.body
    implicitHeight: Theme.buttonHeight
    indicator: Rectangle {
        x: control.leftPadding; y: (control.height - height) / 2
        width: 24; height: 24; radius: 6
        color: control.checked ? Theme.accent : Theme.surface
        border.color: control.activeFocus ? Theme.gold : control.hovered ? Theme.muted : Theme.border
        border.width: control.activeFocus ? 2 : 1
        Rectangle { anchors.centerIn: parent; width: 10; height: 10; radius: 2; color: Theme.accentText; visible: control.checked }
    }
}
