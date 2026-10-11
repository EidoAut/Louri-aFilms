import QtQuick
import ".."

CatalogArtwork {
    objectName: "heroArtwork"
    hero: true
    readonly property bool wideArtwork: ready
    readonly property bool portraitArtwork: ready && !panoramic
}
