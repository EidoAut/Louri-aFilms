import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
Item {
    id: nav
    property Item backdrop
    height: Theme.navHeight
    Rectangle { anchors.fill: parent; color: Theme.background }
    RowLayout {
        anchors.fill: parent; anchors.leftMargin: Theme.margin; anchors.rightMargin: Theme.margin; spacing: Theme.smallGap
        Image { source: brandLogo; Layout.preferredWidth: nav.width < Theme.compactWidth ? 152 : 208; Layout.preferredHeight: Theme.navHeight - Theme.smallGap; fillMode: Image.PreserveAspectFit; sourceSize.width: 624; Layout.rightMargin: nav.width < Theme.compactWidth ? 0 : Theme.gap; Accessible.name: "Louriña Films" }
        Repeater {
            model: ["Home", "Movies", "Series", "Documentaries", "Explore", "My List"]
            delegate: Item {
                required property string modelData
                Layout.preferredWidth: label.implicitWidth + Theme.smallGap; Layout.fillHeight: true
                Rectangle { anchors.centerIn: parent; width: parent.width; height: Theme.buttonHeight; radius: Theme.radius; color: Theme.surface; visible: mouse.containsMouse || mouse.activeFocus; border.color: mouse.activeFocus ? Theme.gold : Theme.transparent }
                Text { font.family: Theme.font; id: label; anchors.centerIn: parent; text: Strings.page(modelData); color: backend.uiState.page === modelData || mouse.containsMouse ? Theme.text : Theme.muted; font.pixelSize: nav.width < Theme.compactWidth ? Theme.caption : Theme.body; font.weight: backend.uiState.page === modelData ? Font.DemiBold : Font.Normal }
                Rectangle { anchors.bottom: parent.bottom; anchors.bottomMargin: Theme.gap; anchors.horizontalCenter: parent.horizontalCenter; width: label.width; height: 2; radius: 1; color: Theme.selection; visible: backend.uiState.page === modelData }
                MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: backend.navigate(modelData); activeFocusOnTab: true; Keys.onReturnPressed: backend.navigate(modelData); Accessible.name: Strings.page(modelData); Accessible.role: Accessible.Button }
            }
        }
        Item { Layout.fillWidth: true }
        ActionButton { text: Strings.page("Search"); onClicked: backend.navigate("Search") }
        ActionButton { text: Strings.page("Settings"); quiet: true; onClicked: backend.navigate("Settings") }
    }
    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
}
