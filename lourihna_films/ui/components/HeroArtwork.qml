import QtQuick
import ".."

Item {
    id: artwork
    objectName: "heroArtwork"
    property var entry: ({})
    readonly property var visual: entry.catalog || entry
    readonly property string sourceKey: [visual.backdrop || "", entry.backdrop || "", visual.poster || "", entry.poster || "", entry.thumbnail_url || ""].join("|")
    readonly property var sources: sourceKey.split("|").filter(function(value, index, values) { return value && values.indexOf(value) === index })
    property int sourceIndex: 0
    onSourceKeyChanged: sourceIndex = 0
    readonly property bool wideArtwork: backdrop.status === Image.Ready
    readonly property bool portraitArtwork: wideArtwork && backdrop.sourceSize.width < backdrop.sourceSize.height

    Rectangle { anchors.fill: parent; color: Theme.background }
    Image {
        id: backdrop
        objectName: "heroBackground"
        anchors.fill: parent
        source: artwork.sources[artwork.sourceIndex] || ""
        asynchronous: true
        fillMode: Image.PreserveAspectCrop
        clip: true
        opacity: artwork.wideArtwork ? 1 : 0
        onStatusChanged: {
            if (status === Image.Error && artwork.sourceIndex + 1 < artwork.sources.length)
                artwork.sourceIndex += 1
        }
        Behavior on opacity { NumberAnimation { duration: Theme.duration } }
    }
    // Keep the full portrait legible while its enlarged crop fills the background.
    Image {
        visible: artwork.portraitArtwork
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.rightMargin: Theme.margin; anchors.topMargin: Theme.navHeight + Theme.gap; anchors.bottomMargin: Theme.gap
        width: parent.width * Theme.heroPortraitWidthRatio
        source: visible ? backdrop.source : ""
        asynchronous: true; fillMode: Image.PreserveAspectFit
    }
}
