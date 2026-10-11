import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "Cinema.js" as Cinema

Popup {
    id: panel
    objectName: "hoverPreview"
    parent: Overlay.overlay
    property var entry: ({})
    property var origin: null
    property var pendingOrigin: null
    property var dismissedOrigin: null
    property var pendingEntry: ({})
    property bool keyboard: false
    property bool suppressReopen: false
    readonly property bool saved: backend.viewState.favorites.some(function (item) {
        return item.key === panel.entry.key;
    })
    width: Math.min(Theme.previewWidth, parent.width - Theme.gap * 2)
    height: body.implicitHeight
    padding: 0
    modal: false
    focus: keyboard
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    Connections {
        target: panel.parent
        function onWidthChanged() {
            panel.dismiss();
        }
        function onHeightChanged() {
            panel.dismiss();
        }
    }
    function schedule(value, anchor) {
        if (cooldown.running || dismissedOrigin === anchor)
            return;
        if (pendingOrigin === anchor && openDelay.running)
            return;
        closeDelay.stop();
        if (visible && origin === anchor)
            return;
        pendingEntry = value;
        pendingOrigin = anchor;
        openDelay.restart();
    }
    function leave(anchor) {
        if (dismissedOrigin === anchor)
            dismissedOrigin = null;
        if (pendingOrigin === anchor) {
            openDelay.stop();
            pendingOrigin = null;
        }
        if (origin === anchor && !keyboard)
            closeDelay.restart();
    }
    function release(anchor) {
        if (origin === anchor || pendingOrigin === anchor)
            dismiss();
    }
    function dismiss() {
        suppressReopen = true;
        openDelay.stop();
        closeDelay.stop();
        pendingOrigin = null;
        close();
    }
    function showEntry(value, anchor, fromKeyboard) {
        if (!anchor || backend.viewState.page === "Details" || backend.viewState.page === "Player")
            return;
        openDelay.stop();
        closeDelay.stop();
        pendingOrigin = null;
        entry = value;
        origin = anchor;
        keyboard = fromKeyboard;
        suppressReopen = false;
        var point = anchor.mapToItem(parent, 0, 0);
        x = Math.max(Theme.gap, Math.min(parent.width - width - Theme.gap, point.x + (anchor.width - width) / 2));
        y = Math.max(Theme.gap, Math.min(parent.height - height - Theme.gap, point.y - Theme.gap));
        open();
        if (keyboard)
            Qt.callLater(function () {
                primary.forceActiveFocus();
            });
    }
    onClosed: {
        openDelay.stop();
        pendingOrigin = null;
        dismissedOrigin = origin;
        if (keyboard || suppressReopen)
            cooldown.restart();
        suppressReopen = false;
        if (keyboard && origin && backend.viewState.page !== "Details" && backend.viewState.page !== "Player")
            origin.forceActiveFocus();
        keyboard = false;
    }
    Timer {
        id: openDelay
        interval: Theme.previewDelay
        onTriggered: panel.showEntry(panel.pendingEntry, panel.pendingOrigin, false)
    }
    Timer {
        id: cooldown
        interval: Theme.previewDelay + Theme.previewCloseDelay
    }
    Timer {
        id: closeDelay
        interval: Theme.previewCloseDelay
        onTriggered: if (!inside.hovered && !panel.keyboard)
            panel.close()
    }
    background: Item {
        Rectangle {
            anchors.fill: parent
            anchors.margins: -8
            y: Theme.shadowOffset
            radius: Theme.heroRadius + 8
            color: Theme.dropShadow
            opacity: 0.25
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: Theme.heroRadius + 3
            color: Theme.dropShadow
        }
        Rectangle {
            anchors.fill: parent
            radius: Theme.heroRadius
            color: Theme.card
            border.color: Theme.border
        }
    }
    contentItem: Column {
        id: body
        width: panel.width
        spacing: 0
        Keys.onEscapePressed: function (event) {
            panel.dismiss();
            event.accepted = true;
        }
        HoverHandler {
            id: inside
            onHoveredChanged: hovered ? closeDelay.stop() : (panel.keyboard ? closeDelay.stop() : closeDelay.restart())
        }
        CatalogArtwork {
            width: parent.width
            height: width * 9 / 16
            entry: panel.entry
            radius: Theme.heroRadius
            surroundColor: Theme.card
        }
        Column {
            x: Theme.previewPadding
            width: parent.width - Theme.previewPadding * 2
            topPadding: Theme.gap
            bottomPadding: Theme.previewPadding
            spacing: Theme.gap
            RowLayout {
                width: parent.width
                spacing: Theme.smallGap
                ActionButton {
                    id: primary
                    objectName: "previewPlay"
                    primary: true
                    circular: true
                    glyph: panel.entry.kind === "video" ? "play" : "search"
                    Accessible.name: panel.entry.kind === "video" ? "Reproducir" : "Buscar fontes"
                    onClicked: {
                        var item = panel.entry;
                        panel.dismiss();
                        item.kind === "video" ? backend.play(item) : cinema.openDetails(item, panel.origin);
                    }
                }
                ActionButton {
                    objectName: "favoriteButton"
                    circular: true
                    glyph: panel.saved ? "check" : "plus"
                    Accessible.name: panel.saved ? "Quitar da miña lista" : "Engadir á miña lista"
                    onClicked: backend.favorite(panel.entry)
                    ToolTip.visible: hovered
                    ToolTip.text: Accessible.name
                }
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    objectName: "previewDetails"
                    circular: true
                    glyph: "down"
                    Accessible.name: "Máis información"
                    onClicked: cinema.openDetails(panel.entry, panel.origin)
                }
            }
            Text {
                width: parent.width
                text: Cinema.title(panel.entry)
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.lead
                font.weight: Font.DemiBold
                maximumLineCount: 2
                wrapMode: Text.Wrap
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            Text {
                width: parent.width
                text: Cinema.metadata(panel.entry)
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.body
                wrapMode: Text.WordWrap
            }
            Text {
                visible: !!text
                width: parent.width
                text: (Cinema.visual(panel.entry).genres || []).slice(0, 3).join(" · ")
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.body
                wrapMode: Text.WordWrap
            }
        }
    }
    enter: Transition {
        NumberAnimation {
            property: "opacity"
            from: 0
            to: 1
            duration: Theme.duration
        }
    }
    exit: Transition {
        NumberAnimation {
            property: "opacity"
            from: 1
            to: 0
            duration: Theme.duration
        }
    }
}
