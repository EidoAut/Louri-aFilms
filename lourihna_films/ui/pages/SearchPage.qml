import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."
import "../components"

ScrollView {
    id: page
    objectName: "searchPage"
    clip: true
    contentWidth: availableWidth
    Connections {
        target: page.contentItem
        function onContentYChanged() {
            var view = page.contentItem;
            if (view.contentY + view.height >= view.contentHeight - Theme.videoHeight && backend.viewState.more && !backend.viewState.busy && !backend.viewState.message)
                backend.more();
        }
    }
    Column {
        x: Theme.gutter(page.width)
        width: page.availableWidth - Theme.gutter(page.width) * 2
        spacing: Theme.gap
        topPadding: Theme.gap
        bottomPadding: Theme.margin
        Text {
            font.family: Theme.font
            text: Strings.t("Encuentra tu próxima historia", "Atopa a túa próxima historia")
            color: Theme.text
            font.pixelSize: Theme.heading
            font.weight: Font.Bold
        }
        RowLayout {
            width: parent.width
            spacing: Theme.smallGap
            TextField {
                id: query
                Layout.fillWidth: true
                implicitHeight: Theme.buttonHeight
                text: backend.viewState.query
                placeholderText: Strings.t("Película, serie o enlace de vídeo", "Película, serie ou ligazón de vídeo")
                selectByMouse: true
                maximumLength: 500
                onAccepted: backend.search(text, "All")
            }
            ActionButton {
                text: Strings.page("Search")
                primary: true
                enabled: query.text.trim().length > 0
                onClicked: backend.search(query.text, "All")
            }
            ActionButton {
                text: Strings.t("Añadir vídeos", "Engadir vídeos")
                Accessible.name: Strings.t("Importar enlaces", "Importar ligazóns")
                onClicked: imports.open()
                Menu {
                    id: imports
                    MenuItem {
                        text: Strings.t("Pegar enlaces", "Pegar ligazóns")
                        onTriggered: importDialog.open()
                    }
                    MenuItem {
                        text: Strings.t("Importar archivo", "Importar ficheiro")
                        onTriggered: fileDialog.open()
                    }
                }
            }
        }
        ActionButton {
            objectName: "clearSearchHistoryButton"
            text: Strings.t("Borrar búsquedas recientes", "Borrar buscas recentes")
            enabled: backend.viewState.recent.length > 0
            onClicked: cinema.openHistory("search")
        }
        Flow {
            width: parent.width
            spacing: Theme.smallGap
            Repeater {
                model: backend.viewState.recent.filter(function (x) {
                    return !query.text || x.toLowerCase().indexOf(query.text.toLowerCase()) >= 0;
                })
                delegate: ActionButton {
                    required property string modelData
                    text: modelData
                    implicitWidth: Math.min(300, contentItem.implicitWidth + 32)
                    onClicked: {
                        query.text = modelData;
                        backend.search(modelData, "All");
                    }
                }
            }
        }
        Text {
            font.family: Theme.font
            font.pixelSize: Theme.body
            width: parent.width
            wrapMode: Text.WordWrap
            text: backend.viewState.results.length ? backend.viewState.results.length + Strings.t(" resultados", " resultados") : backend.viewState.busy ? Strings.t("Buscando…", "Buscando…") : backend.viewState.query ? Strings.t("No hay resultados. Prueba otro título.", "Non hai resultados. Proba outro título.") : Strings.t("Busca un título para empezar.", "Busca un título para comezar.")
            color: Theme.muted
        }
        Flow {
            width: parent.width
            spacing: Theme.gap
            Repeater {
                model: backend.viewState.results
                delegate: VideoCard {
                    required property var modelData
                    entry: modelData
                    landscape: true
                    width: Math.floor((page.availableWidth - Theme.gutter(page.width) * 2 - Theme.gap * (Math.max(2, Math.floor(page.width / 300)) - 1)) / Math.max(2, Math.floor(page.width / 300)))
                }
            }
        }
        ActionButton {
            visible: backend.viewState.more
            text: Strings.t("Ver más", "Ver máis")
            enabled: !backend.viewState.busy
            onClicked: backend.more()
        }
    }
    FileDialog {
        id: fileDialog
        title: Strings.t("Importar enlaces de vídeo", "Importar ligazóns de vídeo")
        nameFilters: ["TXT, HTML, M3U (*.txt *.html *.htm *.m3u *.m3u8)"]
        onAccepted: backend.importFile(selectedFile.toString(), "General")
    }
    Dialog {
        id: importDialog
        objectName: "importDialog"
        title: Strings.t("Añadir vídeos", "Engadir vídeos")
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(700, page.width - Theme.gutter(page.width) * 2)
        onAccepted: {
            backend.importLinks(links.text, category.text);
            links.clear();
        }
        ColumnLayout {
            width: parent.width
            spacing: Theme.smallGap
            Label {
                Layout.fillWidth: true
                text: Strings.t("Pega hasta 100 enlaces públicos de OK.ru, uno por línea.", "Pega ata 100 ligazóns públicas de OK.ru, unha por liña.")
                wrapMode: Text.WordWrap
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                TextArea {
                    id: links
                    placeholderText: "https://ok.ru/video/…"
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                }
            }
            TextField {
                id: category
                Layout.fillWidth: true
                text: "General"
                placeholderText: Strings.t("Categoría", "Categoría")
                maximumLength: 60
            }
        }
        footer: Row {
            spacing: Theme.gap
            padding: Theme.gap
            ActionButton {
                text: Strings.t("Cancelar", "Cancelar")
                onClicked: importDialog.reject()
            }
            ActionButton {
                text: Strings.t("Añadir", "Engadir")
                primary: true
                onClicked: importDialog.accept()
            }
        }
    }
}
