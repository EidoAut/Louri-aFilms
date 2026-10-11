import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Item {
    id: nav
    property Item backdrop
    readonly property string selectedPage: typeof cinema !== "undefined" ? cinema.browsePage : backend.viewState.page
    height: Theme.navHeight
    Rectangle {
        anchors.fill: parent
        color: Theme.background
    }
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Theme.gutter(nav.width)
        anchors.rightMargin: Theme.gutter(nav.width)
        spacing: Theme.smallGap
        Image {
            source: brandLogo
            Layout.preferredWidth: nav.width < Theme.narrowWidth ? 118 : 158
            Layout.preferredHeight: 58
            fillMode: Image.PreserveAspectFit
            sourceSize.width: 474
            Layout.rightMargin: Theme.smallGap
            Accessible.name: "Louriña Films"
        }
        Repeater {
            model: nav.width < Theme.narrowWidth ? ["Home", "Explore", "My List"] : ["Home", "Series", "Movies", "Documentaries", "Explore", "My List"]
            delegate: Button {
                required property string modelData
                text: Strings.page(modelData)
                hoverEnabled: true
                font.family: Theme.font
                font.pixelSize: Theme.body
                padding: Theme.smallGap
                leftPadding: Theme.gap
                rightPadding: Theme.gap
                implicitHeight: Theme.buttonHeight
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: nav.selectedPage === modelData ? Theme.text : Theme.muted
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: height / 2
                    color: nav.selectedPage === modelData ? Theme.card : parent.hovered ? Theme.surface : Theme.transparent
                    border.width: parent.activeFocus ? 2 : 0
                    border.color: Theme.gold
                }
                onClicked: backend.navigate(modelData)
            }
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            glyph: "search"
            quiet: true
            circular: true
            Accessible.name: Strings.page("Search")
            onClicked: backend.navigate("Search")
            ToolTip.visible: hovered
            ToolTip.text: Accessible.name
        }
        ActionButton {
            glyph: "menu"
            quiet: true
            circular: true
            Accessible.name: "Máis seccións"
            onClicked: sections.open()
            Menu {
                id: sections
                MenuItem {
                    text: Strings.page("Series")
                    visible: nav.width < Theme.narrowWidth
                    height: visible ? implicitHeight : 0
                    onClicked: backend.navigate("Series")
                }
                MenuItem {
                    text: Strings.page("Movies")
                    visible: nav.width < Theme.narrowWidth
                    height: visible ? implicitHeight : 0
                    onClicked: backend.navigate("Movies")
                }
                MenuItem {
                    text: Strings.page("Documentaries")
                    visible: nav.width < Theme.narrowWidth
                    height: visible ? implicitHeight : 0
                    onClicked: backend.navigate("Documentaries")
                }
                MenuItem {
                    text: Strings.page("Settings")
                    onClicked: backend.navigate("Settings")
                }
                MenuItem {
                    objectName: "manageHistoryMenu"
                    text: Strings.t("Eliminar historiales…", "Eliminar historiais…")
                    onTriggered: cinema.openHistory("all")
                }
                MenuItem {
                    text: "Actualizar catálogo"
                    visible: ["Home", "Movies", "Series", "Documentaries", "Explore"].indexOf(nav.selectedPage) >= 0
                    height: visible ? implicitHeight : 0
                    onClicked: backend.refreshCatalog()
                }
            }
        }
    }
}
