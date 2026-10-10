import QtQuick
import QtQuick.Controls
import ".."
Item {
    id: card
    required property var entry
    property bool video: entry.kind === "video"
    property bool landscape: video
    readonly property var visual: entry.catalog || entry
    readonly property string displayTitle: entry.local_title ? entry.title : visual.title || entry.title || ""
    property bool saved: backend.uiState.favorites.some(function(x) { return x.key === entry.key })
    width: landscape ? Theme.videoWidth : Theme.cardWidth
    height: landscape ? Theme.videoHeight : Theme.cardHeight
    z: mouse.containsMouse || mouse.activeFocus ? 2 : 0
    Item {
        id: artwork; width: parent.width; height: card.landscape ? Theme.thumbnailHeight : Theme.posterHeight
        scale: mouse.containsMouse || mouse.activeFocus ? Theme.hoverScale : 1
        Behavior on scale { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
        Rectangle { anchors.fill: parent; color: Theme.card; radius: Theme.radius; border.color: mouse.activeFocus ? Theme.gold : Theme.border }
        Image { id: cardImage; anchors.fill: parent; source: card.landscape ? (card.visual.backdrop || card.visual.poster || card.entry.poster || "") : (card.visual.poster || card.entry.poster || ""); asynchronous: true; sourceSize.width: Math.ceil(card.width * Screen.devicePixelRatio); fillMode: Image.PreserveAspectCrop; clip: true }
        Image { anchors.centerIn: parent; width: Math.min(parent.width * 0.28, 64); height: width; source: Theme.symbol; fillMode: Image.PreserveAspectFit; visible: cardImage.status !== Image.Ready; opacity: 0.65 }
        Rectangle { anchors.fill: parent; color: Theme.transparent; border.width: mouse.activeFocus ? 2 : 1; border.color: mouse.activeFocus ? Theme.gold : mouse.containsMouse ? Theme.selection : Theme.border }
        Rectangle { anchors.fill: parent; gradient: Gradient { GradientStop { position: 0.45; color: Theme.transparent } GradientStop { position: 1; color: Theme.heroShade } } }
        Text { font.family: Theme.font; anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: Theme.smallGap; text: card.video ? (entry.provider === "archive" ? "Internet Archive" : "OK.ru") : entry.kind === "tv" ? Strings.t("Serie", "Serie") : Strings.t("Película", "Película"); color: Theme.text; font.pixelSize: Theme.caption }
        Rectangle { anchors.left: parent.left; anchors.bottom: parent.bottom; height: 3; width: parent.width * Math.min(1, (entry.position_ms || 0) / Math.max(1, entry.duration_ms || 0)); color: Theme.red; visible: (entry.position_ms || 0) > 0 && !entry.finished }
    }
    Text { font.family: Theme.font; objectName: "cardTitle"; y: artwork.height + Theme.smallGap; width: parent.width; height: Theme.body * 2.6; clip: true; text: card.displayTitle; color: Theme.text; font.pixelSize: Theme.body; font.weight: Font.DemiBold; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; textFormat: Text.PlainText }
    Text { font.family: Theme.font; anchors.bottom: parent.bottom; anchors.bottomMargin: Theme.smallGap; width: parent.width - footer.width - Theme.smallGap; text: [card.visual.year || "", entry.duration_seconds ? Math.round(entry.duration_seconds / 60) + " min" : ""].filter(Boolean).join(" · "); color: Theme.muted; font.pixelSize: Theme.caption; elide: Text.ElideRight }
    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; activeFocusOnTab: true; onClicked: backend.select(entry); Keys.onReturnPressed: backend.select(entry); Accessible.name: card.displayTitle; Accessible.role: Accessible.Button }
    Row { id: footer; anchors.right: parent.right; anchors.bottom: parent.bottom; spacing: Theme.smallGap
        ActionButton { visible: card.video; text: Strings.t("Ver", "Ver"); quiet: true; implicitHeight: Theme.smallButtonHeight; onClicked: backend.play(entry); Accessible.name: Strings.t("Reproducir", "Reproducir") }
        ActionButton { objectName: "favoriteButton"; text: card.saved ? Strings.t("Quitar", "Quitar") : Strings.t("Añadir", "Engadir"); implicitHeight: Theme.smallButtonHeight; onClicked: backend.favorite(entry); Accessible.name: card.saved ? Strings.t("Quitar de mi lista", "Quitar da miña lista") : Strings.t("Añadir a mi lista", "Engadir á miña lista"); ToolTip.visible: hovered; ToolTip.text: Accessible.name }
    }
}
