import QtQuick
import QtQuick.Controls
import ".."
Column {
    id: carousel
    property string title
    property string subtitle: ""
    property var items: []
    property bool videos: items.length > 0 && !items.every(function(item) { return item.kind !== "video" || !!(item.catalog && item.catalog.poster); })
    width: parent.width; spacing: Theme.gap
    Row {
        width: parent.width; spacing: Theme.smallGap
        Column { width: parent.width - previous.implicitWidth - next.implicitWidth - Theme.smallGap * 2; spacing: Theme.smallGap
            Text { font.family: Theme.font; width: parent.width; elide: Text.ElideRight; text: Strings.page(carousel.title); color: Theme.text; font.pixelSize: Theme.heading * 0.85; font.weight: Font.DemiBold }
            Text { font.family: Theme.font; visible: !!carousel.subtitle; text: carousel.subtitle; color: Theme.muted; font.pixelSize: Theme.caption }
        }
        ActionButton { id: previous; text: Strings.t("Anterior", "Anterior"); onClicked: list.contentX = Math.max(0, list.contentX - list.width * 0.8) }
        ActionButton { id: next; text: Strings.t("Siguiente", "Seguinte"); onClicked: list.contentX = Math.max(0, Math.min(list.contentWidth - list.width, list.contentX + list.width * 0.8)) }
    }
    ListView {
        id: list; width: parent.width; height: (carousel.videos ? Theme.videoHeight : Theme.cardHeight) + Theme.gap; clip: true
        orientation: ListView.Horizontal; spacing: Theme.gap; model: carousel.items; boundsBehavior: Flickable.StopAtBounds
        delegate: VideoCard { required property var modelData; entry: modelData; landscape: carousel.videos; y: Theme.smallGap }
        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }
        Behavior on contentX { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
    }
}
