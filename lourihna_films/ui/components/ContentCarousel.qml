import QtQuick
import QtQuick.Controls
import ".."

Column {
    id: carousel
    objectName: "catalogCarousel"
    property string title
    property string subtitle: ""
    property var items: []
    property bool videos: true
    width: parent.width
    spacing: Theme.smallGap
    Text {
        width: parent.width
        text: Strings.page(carousel.title)
        font.family: Theme.font
        font.pixelSize: Theme.lead + 3
        font.weight: Font.DemiBold
        color: Theme.text
        elide: Text.ElideRight
    }
    Text {
        visible: !!carousel.subtitle
        text: carousel.subtitle
        font.family: Theme.font
        font.pixelSize: Theme.caption
        color: Theme.muted
    }
    Item {
        width: parent.width
        height: Theme.tileWidth(width) * 9 / 16 + Theme.body * 2.4
        HoverHandler {
            id: hovered
        }
        ListView {
            id: list
            objectName: "carouselList"
            anchors.fill: parent
            clip: true
            orientation: ListView.Horizontal
            spacing: Theme.cardGap
            model: carousel.items
            boundsBehavior: Flickable.StopAtBounds
            cacheBuffer: width / 2
            delegate: VideoCard {
                required property var modelData
                required property int index
                carouselIndex: index
                entry: modelData
                width: Theme.tileWidth(list.width)
            }
            onMovementStarted: if (typeof cinema !== "undefined")
                cinema.preview.dismiss()
            WheelHandler {
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                onWheel: function (event) {
                    if (Math.abs(event.angleDelta.x) > Math.abs(event.angleDelta.y) || event.modifiers & Qt.ShiftModifier) {
                        list.contentX = Math.max(0, Math.min(list.contentWidth - list.width, list.contentX - (event.angleDelta.x || event.angleDelta.y)));
                        event.accepted = true;
                    } else
                        event.accepted = false;
                }
            }
        }
        ActionButton {
            anchors.left: parent.left
            y: (parent.height - Theme.body * 2.4 - height) / 2
            glyph: "back"
            circular: true
            Accessible.name: "Anterior"
            visible: list.contentX > 1 && (hovered.hovered || activeFocus)
            onClicked: list.contentX = Math.max(0, list.contentX - list.width * 0.85)
        }
        ActionButton {
            anchors.right: parent.right
            y: (parent.height - Theme.body * 2.4 - height) / 2
            glyph: "forward"
            circular: true
            Accessible.name: "Seguinte"
            visible: list.contentX < list.contentWidth - list.width - 1 && (hovered.hovered || activeFocus)
            onClicked: list.contentX = Math.max(0, Math.min(list.contentWidth - list.width, list.contentX + list.width * 0.85))
        }
    }
}
