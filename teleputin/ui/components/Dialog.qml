import QtQuick
import QtQuick.Controls.Basic as Basic
import ".."
Basic.Dialog {
    padding: Theme.gap
    font.family: Theme.font; font.pixelSize: Theme.body
    background: Rectangle { color: Theme.surface; radius: Theme.radius; border.color: Theme.border }
}
