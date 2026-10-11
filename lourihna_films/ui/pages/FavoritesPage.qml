import QtQuick
import QtQuick.Controls
import ".."
import "../components"

ScrollView {
    id: page
    clip: true
    contentWidth: availableWidth
    Column {
        x: Theme.gutter(page.width)
        width: page.availableWidth - Theme.gutter(page.width) * 2
        spacing: Theme.gap
        topPadding: Theme.margin
        bottomPadding: Theme.margin
        Text {
            font.family: Theme.font
            text: Strings.t("Mi lista", "A miña lista")
            font.pixelSize: Theme.heading
            font.weight: Font.Bold
            color: Theme.text
        }
        Text {
            font.family: Theme.font
            text: backend.viewState.favorites.length ? Strings.t("Abre la ficha de un título para consultar o cambiar tu lista.", "Abre a ficha dun título para consultar ou cambiar a túa lista.") : Strings.t("Busca una película y pulsa Añadir para guardarla aquí.", "Busca unha película e preme Engadir para gardala aquí.")
            width: parent.width
            wrapMode: Text.WordWrap
            color: Theme.muted
            font.pixelSize: 15
        }
        ActionButton {
            objectName: "addToListButton"
            text: Strings.t("Buscar vídeos para añadir", "Buscar vídeos para engadir")
            primary: true
            onClicked: backend.navigate("Search")
        }
        Flow {
            width: parent.width
            spacing: Theme.gap
            Repeater {
                model: backend.viewState.favorites
                delegate: VideoCard {
                    required property var modelData
                    entry: modelData
                    landscape: true
                    width: Math.floor((page.availableWidth - Theme.gutter(page.width) * 2 - Theme.gap * (Math.max(2, Math.floor(page.width / 300)) - 1)) / Math.max(2, Math.floor(page.width / 300)))
                }
            }
        }
        ContentCarousel {
            title: Strings.t("Vistos recientemente", "Vistos recentemente")
            items: backend.viewState.history
            visible: items.length > 0
        }
        ActionButton {
            objectName: "clearWatchHistoryButton"
            text: Strings.t("Borrar historial de reproducción", "Borrar historial de reprodución")
            enabled: backend.viewState.history.length > 0
            onClicked: cinema.openHistory("watch")
        }
    }
}
