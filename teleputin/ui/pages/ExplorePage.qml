import QtQuick
import QtQuick.Controls
import ".."
import "../components"
GridView {
    id: grid
    objectName: "exploreGrid"
    clip: true
    leftMargin: Theme.margin
    rightMargin: Theme.margin
    readonly property int columns: Math.max(1, Math.floor((width - Theme.margin * 2) / (Theme.videoWidth + Theme.gap)))
    cellWidth: (width - Theme.margin * 2) / columns
    cellHeight: Theme.videoHeight + Theme.gap
    cacheBuffer: height
    ListModel { id: videoModel }
    model: videoModel
    property bool syncingItems: false
    property real previousY: contentY
    property int lastRequestedCount: -1
    function syncItems() {
        syncingItems = true
        // Materialize once: delegates must not repeatedly convert the full Python list.
        var items = JSON.parse(backend.exploreItemsJson)
        var reset = items.length < videoModel.count
        for (var i = 0; !reset && i < videoModel.count; ++i)
            reset = videoModel.get(i).videoKey !== items[i].key
        if (reset) { videoModel.clear(); lastRequestedCount = -1 }
        for (var j = 0; j < items.length; ++j) {
            var encoded = JSON.stringify(items[j])
            if (j >= videoModel.count)
                videoModel.append({videoKey: items[j].key, entryJson: encoded})
            else if (videoModel.get(j).entryJson !== encoded)
                videoModel.setProperty(j, "entryJson", encoded)
        }
        syncingItems = false
    }
    Component.onCompleted: syncItems()
    ScrollBar.vertical: ScrollBar {}
    function loadNearEnd() {
        if (!syncingItems && contentY + height >= contentHeight - cellHeight
                && videoModel.count !== lastRequestedCount
                && backend.uiState.exploreMore && !backend.uiState.busy && !backend.uiState.exploreError) {
            lastRequestedCount = videoModel.count
            backend.moreExplore()
        }
    }
    onContentYChanged: {
        var movedDown = contentY > previousY
        previousY = contentY
        if (movedDown && !syncingItems) Qt.callLater(grid.loadNearEnd)
    }
    Connections {
        target: backend
        function onExploreItemsChanged() { Qt.callLater(grid.syncItems) }
    }
    header: Column {
        width: grid.width - Theme.margin * 2
        spacing: Theme.gap
        topPadding: Theme.gap
        bottomPadding: Theme.gap
        Text { font.family: Theme.font; text: Strings.page("Explore"); font.pixelSize: Theme.heading; color: Theme.text }
        ActionButton { text: Strings.t("Actualizar catálogo", "Actualizar catálogo"); enabled: !backend.uiState.busy; onClicked: { grid.positionViewAtBeginning(); backend.refreshCatalog() } }
    }
    delegate: Item {
        required property string entryJson
        width: grid.cellWidth
        height: grid.cellHeight
        VideoCard { entry: JSON.parse(parent.entryJson); landscape: true; width: grid.cellWidth - Theme.gap }
    }
    footer: Column {
        // Stable geometry prevents scroll jumps when loading controls change.
        height: Theme.buttonHeight + Theme.body * 3 + Theme.gap * 2 + Theme.margin
        width: grid.width - Theme.margin * 2
        spacing: Theme.gap
        bottomPadding: Theme.margin
        Text { font.family: Theme.font; font.pixelSize: Theme.body;
            width: parent.width; wrapMode: Text.WordWrap; color: Theme.muted
            text: backend.uiState.busy ? Strings.t("Cargando más vídeos…", "Cargando máis vídeos…") : backend.uiState.exploreError ? Strings.t("No se pudieron cargar todas las fuentes.", "Non se puideron cargar todas as fontes.") : backend.uiState.exploreMore ? "" : Strings.t("No hay más vídeos disponibles por ahora.", "Non hai máis vídeos dispoñibles polo de agora.")
        }
        ActionButton {
            visible: backend.uiState.exploreMore && !backend.uiState.exploreError
            enabled: !backend.uiState.busy
            text: Strings.t("Cargar más vídeos", "Cargar máis vídeos")
            onClicked: backend.moreExplore()
        }
        ActionButton { visible: backend.uiState.exploreError; enabled: !backend.uiState.busy; text: Strings.t("Reintentar", "Tentar de novo"); onClicked: backend.uiState.exploreNumber ? backend.moreExplore() : backend.refreshCatalog() }
    }
}
