import QtQuick
import QtQuick.Controls.Basic as Basic
import ".."
Basic.ComboBox {
    id: control
    implicitHeight: Theme.buttonHeight
    implicitWidth: 180
    contentItem: Text { leftPadding: Theme.smallGap; rightPadding: Theme.gap; text: control.displayText; font: control.font; color: control.enabled ? Theme.text : Theme.muted; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
    font.family: Theme.font
    font.pixelSize: Theme.body
    hoverEnabled: true
    background: Rectangle {
        radius: Theme.buttonRadius; color: control.enabled ? Theme.surface : Theme.background
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.gold : control.hovered ? Theme.muted : Theme.border
    }
}
