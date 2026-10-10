import QtQuick
import QtQuick.Controls
import ".."
import "../components"
ScrollView {
    id: page; clip: true; contentWidth: availableWidth
    Column {
        x: Theme.margin; width: page.availableWidth - Theme.margin * 2; spacing: Theme.gap; topPadding: Theme.margin; bottomPadding: Theme.margin
        Text { font.family: Theme.font; text: Strings.t("Mi lista", "A miña lista"); font.pixelSize: Theme.heading; font.weight: Font.Bold; color: Theme.text }
        Text { font.family: Theme.font; text: backend.uiState.favorites.length ? Strings.t("Pulsa Quitar para sacar un vídeo de tu lista.", "Preme Quitar para sacar un vídeo da túa lista.") : Strings.t("Busca una película y pulsa Añadir para guardarla aquí.", "Busca unha película e preme Engadir para gardala aquí."); width: parent.width; wrapMode: Text.WordWrap; color: Theme.muted; font.pixelSize: 15 }
        ActionButton { objectName: "addToListButton"; text: Strings.t("Buscar vídeos para añadir", "Buscar vídeos para engadir"); primary: true; onClicked: backend.navigate("Search") }
        Flow { width: parent.width; spacing: Theme.gap; Repeater { model: backend.uiState.favorites; delegate: VideoCard { required property var modelData; entry: modelData; landscape: true } } }
        ContentCarousel { title: Strings.t("Vistos recientemente", "Vistos recentemente"); items: backend.uiState.history; visible: items.length > 0 }
    }
}
