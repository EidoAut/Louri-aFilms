import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
ScrollView {
    id: page; objectName: "detailsPage"; clip: true; contentWidth: availableWidth
    property var entry: backend.uiState.details
    property bool isVideo: entry.kind === "video"
    property var visual: entry.catalog || entry
    Column {
        width: page.availableWidth; spacing: Theme.gap
        Item {
            width: parent.width; height: Math.max(Theme.heroMin, copy.implicitHeight + Theme.navHeight + Theme.gap * 2)
            HeroArtwork { id: detailArtwork; anchors.fill: parent; entry: page.visual }
            Rectangle { visible: detailArtwork.wideArtwork; anchors.fill: parent; gradient: Gradient { orientation: Gradient.Horizontal; GradientStop { position: 0; color: Theme.background } GradientStop { position: 1; color: Theme.transparent } } }
            Rectangle { visible: detailArtwork.wideArtwork; anchors.fill: parent; gradient: Gradient { GradientStop { position: 0.3; color: Theme.transparent } GradientStop { position: 1; color: Theme.background } } }
            Column {
                id: copy; anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: Theme.margin; anchors.bottomMargin: Theme.gap * 2
                width: Math.min(parent.width - Theme.margin * 2, Theme.textMaxWidth); spacing: Theme.gap
                Text { font.family: Theme.font; text: page.isVideo ? page.entry.provider === "archive" ? "Internet Archive" : "OK.ru" : Strings.t("Descubre la película", "Descubre a película"); color: Theme.muted; font.pixelSize: Theme.body }
                Text { font.family: Theme.font; width: parent.width; text: page.entry.local_title ? page.entry.title : page.visual.title || ""; color: Theme.text; font.pixelSize: page.width < Theme.compactWidth ? Theme.display * 0.7 : Theme.display; font.weight: Font.Bold; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight; textFormat: Text.PlainText }
                Text { font.family: Theme.font; font.pixelSize: Theme.body; width: parent.width; text: [page.visual.year || "", (page.visual.genres || []).slice(0,3).join(" · "), page.visual.rating ? "TMDB " + Number(page.visual.rating).toFixed(1) : ""].filter(Boolean).join("  ·  "); color: Theme.muted; wrapMode: Text.WordWrap }
                Text { font.family: Theme.font; width: parent.width; text: page.visual.overview || page.entry.description || Strings.t("Sin sinopsis disponible.", "Sen sinopse dispoñible."); color: Theme.text; font.pixelSize: Theme.lead; wrapMode: Text.WordWrap; maximumLineCount: 5; elide: Text.ElideRight; textFormat: Text.PlainText; lineHeight: 1.3 }
                Text { font.family: Theme.font; width: parent.width; wrapMode: Text.WordWrap; visible: !!page.visual.overview_translated || !!page.visual.translation_notice; text: page.visual.overview_translated ? Strings.t("Traducción automática local", "Tradución automática local") : Strings.t("No se pudo traducir. Se muestra la sinopsis disponible.", "Non se puido traducir. Amósase a sinopse dispoñible."); color: Theme.muted; font.pixelSize: Theme.caption }
                Flow { width: parent.width; spacing: Theme.smallGap
                    ActionButton { primary: true; text: page.isVideo ? Strings.t("Reproducir", "Reproducir") : Strings.t("Ver fuentes", "Ver fontes"); enabled: !backend.uiState.candidatesBusy; onClicked: page.isVideo ? backend.play(page.entry) : backend.findCandidates() }
                    ActionButton { text: backend.uiState.favorites.some(function(x) { return x.key === page.entry.key }) ? Strings.t("Quitar de mi lista", "Quitar da miña lista") : Strings.t("Añadir a mi lista", "Engadir á miña lista"); onClicked: backend.favorite(page.entry) }
                    ActionButton { text: Strings.t("Más opciones", "Máis opcións"); onClicked: tools.open()
                        Menu { id: tools
                            MenuItem { text: Strings.t("Organizar", "Organizar"); visible: page.isVideo; onTriggered: organize.open() }
                            MenuItem { text: Strings.t("Actualizar información", "Actualizar información"); visible: page.isVideo; onTriggered: backend.refreshMetadata() }
                            MenuItem { text: Strings.t("Página original", "Páxina orixinal"); visible: page.isVideo; onTriggered: backend.openExternal(page.entry.original_url) }
                        }
                    }
                    ActionButton { text: Strings.t("Volver", "Volver"); onClicked: backend.backFromDetails() }
                }
            }
        }
        Column {
            x: Theme.margin; width: parent.width - Theme.margin * 2; spacing: Theme.gap; bottomPadding: Theme.margin
            Text { font.family: Theme.font; visible: !page.isVideo; text: Strings.t("Dónde verla", "Onde vela"); color: Theme.text; font.pixelSize: Theme.heading }
            Text { font.family: Theme.font; font.pixelSize: Theme.body; visible: !page.isVideo; width: parent.width; text: backend.uiState.candidatesBusy ? Strings.t("Buscando vídeos…", "Buscando vídeos…") : backend.uiState.candidates.length ? Strings.t("Elige una fuente y comprueba que sea el título que buscas.", "Escolle unha fonte e comproba que sexa o título que buscas.") : Strings.t("No hemos encontrado vídeos. Prueba otro título en Buscar.", "Non atopamos vídeos. Proba outro título en Buscar."); color: Theme.muted; wrapMode: Text.WordWrap }
            Repeater { model: backend.uiState.candidates || []
                delegate: Rectangle {
                    required property var modelData
                    width: parent.width; height: row.implicitHeight + Theme.gap * 2; radius: Theme.radius; color: Theme.surface
                    RowLayout { id: row; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: Theme.gap; spacing: Theme.gap
                        Image { source: modelData.poster || ""; Layout.preferredWidth: Theme.episodeImageWidth; Layout.preferredHeight: Theme.episodeImageHeight; fillMode: Image.PreserveAspectCrop; clip: true; asynchronous: true }
                        ColumnLayout { Layout.fillWidth: true
                            Text { font.family: Theme.font; Layout.fillWidth: true; text: modelData.title; color: Theme.text; font.pixelSize: Theme.lead; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight; textFormat: Text.PlainText }
                            Text { font.family: Theme.font; font.pixelSize: Theme.body; text: (modelData.provider === "archive" ? "Internet Archive" : "OK.ru") + (modelData.duration_seconds ? " · " + Math.round(modelData.duration_seconds / 60) + " min" : ""); color: Theme.muted }
                        }
                        ActionButton { text: Strings.t("Reproducir", "Reproducir"); primary: true; onClicked: backend.play(modelData) }
                    }
                }
            }
            Text { font.family: Theme.font; visible: page.entry.kind === "tv"; text: Strings.t("Temporadas y episodios", "Tempadas e episodios"); font.pixelSize: Theme.heading; color: Theme.text }
            Flow { width: parent.width; spacing: Theme.smallGap
                Repeater { model: page.entry.seasons || []; delegate: ActionButton { required property var modelData; text: modelData.name; onClicked: backend.season(modelData.season_number) } }
            }
            Repeater { model: backend.uiState.episodes
                delegate: Rectangle {
                    required property var modelData
                    width: parent.width; height: episodeRow.implicitHeight + Theme.gap * 2; color: Theme.surface; radius: Theme.radius
                    RowLayout { id: episodeRow; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: Theme.gap; spacing: Theme.gap
                        ColumnLayout { Layout.fillWidth: true
                            Text { font.family: Theme.font; Layout.fillWidth: true; text: modelData.episode_number + ". " + modelData.name; color: Theme.text; font.pixelSize: Theme.lead; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
                            Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; text: modelData.overview || ""; color: Theme.muted; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight; textFormat: Text.PlainText }
                        }
                        ActionButton { text: Strings.t("Buscar episodio", "Buscar episodio"); onClicked: backend.findEpisode(modelData) }
                    }
                }
            }
            ContentCarousel { title: Strings.t("También te puede gustar", "Tamén che pode gustar"); items: page.visual.related || []; visible: items.length > 0 }
        }
    }
    Dialog { id: organize; modal: true; anchors.centerIn: Overlay.overlay; title: Strings.t("Organizar vídeo", "Organizar vídeo"); standardButtons: Dialog.Save | Dialog.Cancel
        onAccepted: backend.organize(page.entry.key, localTitle.text, localCategory.text)
        ColumnLayout {
            TextField { id: localTitle; text: page.entry.title || ""; placeholderText: Strings.t("Título", "Título"); maximumLength: 1000; Layout.preferredWidth: 380 }
            TextField { id: localCategory; text: page.entry.category || "General"; placeholderText: Strings.t("Categoría", "Categoría"); maximumLength: 60; Layout.fillWidth: true }
        }
    }
}
