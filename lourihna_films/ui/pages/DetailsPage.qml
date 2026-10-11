import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../components/Cinema.js" as Cinema

ScrollView {
    id: page
    objectName: "detailsPage"
    clip: true
    contentWidth: availableWidth
    property var entry: backend.viewState.details
    readonly property bool isVideo: entry.kind === "video"
    readonly property var visual: entry.catalog || entry
    readonly property var progress: Cinema.progress(entry, backend.viewState.history || [])
    readonly property int inset: width < Theme.narrowWidth ? Theme.gap * 1.5 : Theme.margin
    property int selectedSeason: -1
    onEntryChanged: if ((entry.seasons || []).length && selectedSeason < 0)
        selectedSeason = 0
    Column {
        width: page.availableWidth
        spacing: Theme.sectionGap
        bottomPadding: Theme.margin
        Item {
            width: parent.width
            height: Math.max(340, Math.min(530, width * 0.53))
            HeroArtwork {
                anchors.fill: parent
                entry: page.entry
                hero: true
                radius: Theme.heroRadius
            }
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop {
                        position: 0.15
                        color: Theme.transparent
                    }
                    GradientStop {
                        position: 1
                        color: Theme.surface
                    }
                }
            }
            Rectangle {
                anchors.fill: parent
                radius: Theme.heroRadius
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop {
                        position: 0
                        color: Theme.heroShade
                    }
                    GradientStop {
                        position: 1
                        color: Theme.transparent
                    }
                }
            }
            Column {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: page.inset
                anchors.bottomMargin: Theme.smallGap
                spacing: Theme.gap
                Text {
                    text: page.isVideo ? (page.entry.provider === "archive" ? "INTERNET ARCHIVE" : "OK.RU") : "LOURIÑA FILMS"
                    color: Theme.accent
                    font.family: Theme.font
                    font.pixelSize: Theme.caption
                    font.letterSpacing: 2
                }
                Text {
                    width: parent.width
                    text: Cinema.title(page.entry)
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: page.width < Theme.narrowWidth ? Theme.compactDisplay : Theme.display * 0.85
                    font.weight: Font.Bold
                    wrapMode: Text.Wrap
                    maximumLineCount: 3
                    elide: Text.ElideRight
                    textFormat: Text.PlainText
                }
                RowLayout {
                    width: Math.min(500, parent.width)
                    visible: Cinema.resumable(page.progress) && (page.progress.duration_ms || 0) > 0
                    spacing: Theme.smallGap
                    Rectangle {
                        Layout.fillWidth: true
                        height: 3
                        radius: 2
                        color: Theme.border
                        Rectangle {
                            width: parent.width * Math.min(1, (page.progress.position_ms || 0) / Math.max(1, page.progress.duration_ms || 0))
                            height: parent.height
                            radius: 2
                            color: Theme.accent
                        }
                    }
                    Text {
                        text: Math.floor((page.progress.position_ms || 0) / 60000) + " de " + Math.round((page.progress.duration_ms || 0) / 60000) + " min"
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                    }
                }
                Flow {
                    width: parent.width
                    spacing: Theme.smallGap
                    ActionButton {
                        objectName: "detailsPlay"
                        primary: true
                        glyph: page.isVideo ? "play" : "search"
                        text: page.isVideo ? (Cinema.resumable(page.progress) ? "Continuar" : "Reproducir") : "Buscar fontes"
                        enabled: !backend.viewState.candidatesBusy
                        onClicked: page.isVideo ? backend.play(page.entry) : backend.findCandidates()
                    }
                    ActionButton {
                        objectName: "detailsFavorite"
                        circular: true
                        glyph: backend.viewState.favorites.some(function (x) {
                            return x.key === page.entry.key;
                        }) ? "check" : "plus"
                        Accessible.name: "Engadir ou quitar da miña lista"
                        onClicked: backend.favorite(page.entry)
                        ToolTip.visible: hovered
                        ToolTip.text: Accessible.name
                    }
                    ActionButton {
                        text: "Máis opcións"
                        onClicked: tools.open()
                        Menu {
                            id: tools
                            MenuItem {
                                text: "Organizar"
                                visible: page.isVideo
                                height: visible ? implicitHeight : 0
                                onClicked: organize.open()
                            }
                            MenuItem {
                                text: "Actualizar información"
                                visible: page.isVideo
                                height: visible ? implicitHeight : 0
                                onClicked: backend.refreshMetadata()
                            }
                            MenuItem {
                                text: "Páxina orixinal"
                                visible: page.isVideo
                                height: visible ? implicitHeight : 0
                                onClicked: backend.openExternal(page.entry.original_url)
                            }
                            MenuItem {
                                text: "Pechar ficha"
                                onClicked: backend.backFromDetails()
                            }
                        }
                    }
                }
            }
        }
        Column {
            x: page.inset
            width: parent.width - page.inset * 2
            spacing: Theme.sectionGap
            GridLayout {
                width: parent.width
                columns: page.width < Theme.narrowWidth ? 1 : 2
                columnSpacing: Theme.sectionGap
                rowSpacing: Theme.gap
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: page.width * 0.58
                    Layout.alignment: Qt.AlignTop
                    spacing: Theme.gap
                    Text {
                        Layout.fillWidth: true
                        text: Cinema.metadata(page.entry)
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.visual.overview || page.entry.description || "Sen sinopse dispoñible."
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.lead
                        wrapMode: Text.WordWrap
                        textFormat: Text.PlainText
                        lineHeight: 1.35
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: !!page.visual.overview_translated || !!page.visual.translation_notice
                        text: page.visual.overview_translated ? "Tradución automática local" : "Amósase a sinopse dispoñible."
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.caption
                        wrapMode: Text.WordWrap
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: page.width * 0.25
                    Layout.alignment: Qt.AlignTop
                    spacing: Theme.gap
                    Text {
                        Layout.fillWidth: true
                        visible: !!text
                        text: (page.visual.genres || []).length ? "Xéneros: " + page.visual.genres.join(", ") : ""
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: !!text
                        text: (page.visual.directors || []).length ? "Dirección: " + page.visual.directors.join(", ") : ""
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                        textFormat: Text.PlainText
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: !!page.visual.original_title && page.visual.original_title !== page.visual.title
                        text: "Título orixinal: " + (page.visual.original_title || "")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                        textFormat: Text.PlainText
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.isVideo ? "Fonte do vídeo: " + (page.entry.provider === "archive" ? "Internet Archive" : "OK.ru") : "Ficha de catálogo. A reprodución depende das fontes dispoñibles."
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                    }
                }
            }
            Column {
                width: parent.width
                spacing: Theme.gap
                visible: !page.isVideo
                Text {
                    text: "Onde vela"
                    font.family: Theme.font
                    font.pixelSize: Theme.heading
                    font.weight: Font.DemiBold
                    color: Theme.text
                }
                RowLayout {
                    width: parent.width
                    LoadingIndicator {
                        visible: backend.viewState.candidatesBusy
                        running: visible
                        width: 24
                        height: 24
                    }
                    Text {
                        Layout.fillWidth: true
                        text: backend.viewState.candidatesBusy ? "Buscando vídeos…" : backend.viewState.candidates.length ? "Escolle unha fonte e comproba que corresponde á obra." : "Aínda non hai unha fonte dispoñible. Podes buscar de novo."
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.body
                        wrapMode: Text.WordWrap
                    }
                }
                Repeater {
                    model: backend.viewState.candidates || []
                    delegate: Rectangle {
                        required property var modelData
                        width: parent.width
                        height: candidateRow.implicitHeight + Theme.gap * 2
                        radius: Theme.radius
                        color: Theme.card
                        RowLayout {
                            id: candidateRow
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: Theme.gap
                            spacing: Theme.gap
                            CatalogArtwork {
                                visible: page.width >= Theme.narrowWidth
                                entry: modelData
                                Layout.preferredWidth: 140
                                Layout.preferredHeight: 79
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.title
                                    font.family: Theme.font
                                    font.pixelSize: Theme.body
                                    font.weight: Font.DemiBold
                                    color: Theme.text
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                    textFormat: Text.PlainText
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: (modelData.provider === "archive" ? "Internet Archive" : "OK.ru") + (modelData.duration_seconds ? " · " + Math.round(modelData.duration_seconds / 60) + " min de vídeo" : "")
                                    color: Theme.muted
                                    font.family: Theme.font
                                    font.pixelSize: Theme.caption
                                    wrapMode: Text.WordWrap
                                }
                            }
                            ActionButton {
                                primary: true
                                circular: true
                                glyph: "play"
                                Accessible.name: "Reproducir " + modelData.title
                                onClicked: backend.play(modelData)
                            }
                        }
                    }
                }
            }
            Column {
                width: parent.width
                spacing: Theme.gap
                visible: page.entry.kind === "tv" && (page.entry.seasons || []).length > 0
                RowLayout {
                    width: parent.width
                    Text {
                        Layout.fillWidth: true
                        text: "Episodios"
                        font.family: Theme.font
                        font.pixelSize: Theme.heading
                        color: Theme.text
                        font.weight: Font.DemiBold
                    }
                    ComboBox {
                        objectName: "seasonSelector"
                        model: page.entry.seasons || []
                        textRole: "name"
                        currentIndex: page.selectedSeason
                        Layout.preferredWidth: Math.min(240, page.width * 0.4)
                        Accessible.name: "Tempada"
                        onActivated: {
                            page.selectedSeason = currentIndex;
                            backend.season(model[currentIndex].season_number);
                        }
                    }
                }
                Text {
                    visible: !(backend.viewState.episodes || []).length
                    text: backend.viewState.busy ? "Cargando episodios…" : "Escolle unha tempada para consultar os episodios."
                    font.family: Theme.font
                    font.pixelSize: Theme.body
                    color: Theme.muted
                }
                Repeater {
                    model: backend.viewState.episodes || []
                    delegate: Rectangle {
                        required property var modelData
                        width: parent.width
                        height: episodeRow.implicitHeight + Theme.gap * 2
                        color: Theme.card
                        radius: Theme.radius
                        RowLayout {
                            id: episodeRow
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: Theme.gap
                            spacing: Theme.gap
                            Text {
                                text: modelData.episode_number
                                font.family: Theme.font
                                font.pixelSize: Theme.lead
                                color: Theme.muted
                            }
                            CatalogArtwork {
                                visible: !!modelData.still
                                entry: modelData
                                Layout.preferredWidth: page.width < Theme.narrowWidth ? 90 : 160
                                Layout.preferredHeight: width * 9 / 16
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Theme.smallGap
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    font.family: Theme.font
                                    font.pixelSize: Theme.body
                                    font.weight: Font.DemiBold
                                    color: Theme.text
                                    wrapMode: Text.Wrap
                                    textFormat: Text.PlainText
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: !!modelData.runtime
                                    text: (modelData.runtime || "") + " min"
                                    font.family: Theme.font
                                    font.pixelSize: Theme.caption
                                    color: Theme.muted
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.overview || ""
                                    visible: !!text
                                    font.family: Theme.font
                                    font.pixelSize: Theme.body
                                    color: Theme.muted
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 3
                                    elide: Text.ElideRight
                                    textFormat: Text.PlainText
                                }
                            }
                            ActionButton {
                                glyph: "search"
                                circular: true
                                Accessible.name: "Buscar episodio " + modelData.episode_number
                                onClicked: backend.findEpisode(modelData)
                            }
                        }
                    }
                }
            }
            ContentCarousel {
                title: "Outros títulos do catálogo"
                items: page.visual.related || []
                visible: items.length > 0
            }
        }
    }
    Dialog {
        id: organize
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(440, page.width - Theme.gap * 2)
        title: "Organizar vídeo"
        standardButtons: Dialog.Save | Dialog.Cancel
        onAccepted: backend.organize(page.entry.key, localTitle.text, localCategory.text)
        ColumnLayout {
            width: parent.width
            TextField {
                id: localTitle
                text: page.entry.title || ""
                placeholderText: "Título"
                maximumLength: 1000
                Layout.fillWidth: true
            }
            TextField {
                id: localCategory
                text: page.entry.category || "General"
                placeholderText: "Categoría"
                maximumLength: 60
                Layout.fillWidth: true
            }
        }
    }
}
