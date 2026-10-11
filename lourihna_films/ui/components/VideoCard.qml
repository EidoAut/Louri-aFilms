import QtQuick
import QtQuick.Controls
import ".."
import "Cinema.js" as Cinema

FocusScope {
    id: card
    objectName: "catalogCard"
    required property var entry
    property bool video: entry.kind === "video"
    property bool landscape: true
    property int carouselIndex: -1
    readonly property var visual: entry.catalog || entry
    readonly property string displayTitle: Cinema.title(entry)
    readonly property bool saved: backend.viewState.favorites.some(function (x) {
        return x.key === entry.key;
    })
    width: Theme.videoWidth
    height: width * 9 / 16 + Theme.body * 2.4
    function openPreview() {
        if (typeof cinema !== "undefined")
            cinema.preview.showEntry(entry, card, true);
    }
    function moveInRow(delta) {
        var view = card.ListView.view;
        if (!view || carouselIndex < 0)
            return;
        view.currentIndex = Math.max(0, Math.min(view.count - 1, carouselIndex + delta));
        view.positionViewAtIndex(view.currentIndex, ListView.Contain);
        if (view.currentItem)
            view.currentItem.forceActiveFocus();
    }
    CatalogArtwork {
        id: artwork
        width: parent.width
        height: width * 9 / 16
        entry: card.entry
    }
    Rectangle {
        anchors.fill: artwork
        radius: Theme.radius
        color: Theme.transparent
        border.width: mouse.activeFocus ? 2 : 0
        border.color: Theme.gold
    }
    Rectangle {
        x: Theme.smallGap
        y: artwork.height - 4
        width: (artwork.width - Theme.smallGap * 2) * Math.min(1, (entry.position_ms || 0) / Math.max(1, entry.duration_ms || 0))
        height: 3
        radius: 2
        color: Theme.accent
        visible: Cinema.resumable(entry)
    }
    Text {
        objectName: "cardTitle"
        x: 2
        y: artwork.height + Theme.smallGap
        width: parent.width - 4
        text: card.displayTitle
        color: Theme.text
        font.family: Theme.font
        font.pixelSize: Theme.body
        font.weight: Font.Medium
        elide: Text.ElideRight
        textFormat: Text.PlainText
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        activeFocusOnTab: true
        focus: true
        Accessible.name: card.displayTitle
        Accessible.role: Accessible.Button
        onEntered: if (typeof cinema !== "undefined")
            cinema.preview.schedule(entry, card)
        onPositionChanged: if (containsMouse && typeof cinema !== "undefined")
            cinema.preview.schedule(entry, card)
        onExited: if (typeof cinema !== "undefined")
            cinema.preview.leave(card)
        onClicked: function (event) {
            mouse.forceActiveFocus();
            cinema.openDetails(entry, card);
        }
        Keys.onReturnPressed: cinema.openDetails(entry, card)
        Keys.onSpacePressed: card.openPreview()
        Keys.onDownPressed: card.openPreview()
        Keys.onRightPressed: card.moveInRow(1)
        Keys.onLeftPressed: card.moveInRow(-1)
    }
    Component.onDestruction: if (typeof cinema !== "undefined")
        cinema.preview.release(card)
}
