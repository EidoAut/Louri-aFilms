import QtQuick
import QtQuick.Controls.Basic as Basic
import ".."
Basic.TextField {
    id: control
    implicitHeight: Theme.buttonHeight
    font.family: Theme.font
    font.pixelSize: Theme.body
    hoverEnabled: true
    background: Rectangle {
        radius: Theme.buttonRadius; color: control.enabled ? Theme.surface : Theme.background
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.gold : control.hovered ? Theme.muted : Theme.border
    }
}
