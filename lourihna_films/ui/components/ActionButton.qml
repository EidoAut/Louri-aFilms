import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control
    property bool primary: false
    property string glyph: ""
    property bool quiet: false
    property bool circular: false
    implicitHeight: Theme.buttonHeight
    implicitWidth: glyph && !text ? Theme.buttonHeight : Math.max(80, contentItem.implicitWidth + Theme.gap * 2)
    font.family: Theme.font
    font.pixelSize: Theme.body
    font.weight: primary ? Font.DemiBold : Font.Medium
    hoverEnabled: true
    contentItem: Item {
        implicitWidth: label.implicitWidth + (control.glyph ? Theme.iconSize + (control.text ? Theme.smallGap : 0) : 0)
        implicitHeight: Theme.iconSize
        Row {
            anchors.centerIn: parent
            spacing: control.text && control.glyph ? Theme.smallGap : 0
            Image {
                visible: !!control.glyph
                width: visible ? Theme.iconSize : 0
                height: Theme.iconSize
                source: control.glyph ? "../../assets/icons/" + control.glyph + ".svg" : ""
                opacity: control.enabled ? 1 : 0.4
            }
            Text {
                id: label
                text: control.text
                color: !control.enabled ? Theme.muted : control.primary ? Theme.accentText : Theme.text
                font: control.font
                height: Theme.iconSize
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
    background: Rectangle {
        radius: control.circular ? height / 2 : Theme.buttonRadius
        color: control.down ? Theme.selected : control.primary ? (control.hovered ? Theme.hover : Theme.accent) : control.hovered ? Theme.card : control.quiet ? Theme.transparent : Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.gold : control.primary ? color : control.hovered ? Theme.muted : control.quiet ? Theme.transparent : Theme.border
        Behavior on color {
            ColorAnimation {
                duration: Theme.duration
            }
        }
        opacity: control.enabled ? 1 : 0.5
    }
}
