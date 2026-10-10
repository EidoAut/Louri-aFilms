import QtQuick
import QtQuick.Controls
import ".."
import "../components"
ScrollView {
    id: page; clip: true; contentWidth: availableWidth
    property int spotlight: 0
    property var featured: backend.uiState.rows.length ? backend.uiState.rows[0].items.slice(0, 5) : []
    Column {
        width: page.availableWidth; spacing: Theme.gap
        FeaturedBanner { entry: page.featured.length ? page.featured[page.spotlight % page.featured.length] : ({}) }
        Column {
            x: Theme.margin; width: parent.width - Theme.margin * 2; spacing: Theme.gap; bottomPadding: Theme.margin
            Item { width: parent.width; height: Theme.buttonHeight
                Row { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; spacing: Theme.smallGap
                    Repeater { model: page.featured.length; delegate: Rectangle { required property int index; width: page.spotlight === index ? 26 : 8; height: 4; radius: 2; color: page.spotlight === index ? Theme.text : Theme.muted
                        MouseArea { anchors.fill: parent; anchors.margins: -8; cursorShape: Qt.PointingHandCursor; activeFocusOnTab: true; onClicked: page.spotlight = index; Keys.onReturnPressed: page.spotlight = index; Accessible.name: Strings.t("Destacado ", "Destacado ") + (index + 1) }
                    } }
                }
                ActionButton { anchors.right: parent.right; text: Strings.t("Opciones", "Opcións"); Accessible.name: Strings.t("Opciones del catálogo", "Opcións do catálogo"); onClicked: catalogMenu.open()
                    Menu { id: catalogMenu; MenuItem { text: Strings.t("Actualizar catálogo", "Actualizar catálogo"); onTriggered: backend.refreshCatalog() } }
                }
            }
            ContentCarousel { title: Strings.t("Continuar viendo", "Seguir vendo"); subtitle: ""; items: (backend.uiState.continuing || []).filter(function(x) { return (x.position_ms || 0) > 0 }); visible: items.length > 0 && backend.uiState.page === "Home" }
            ContentCarousel { title: Strings.t("Pendientes", "Pendentes"); items: (backend.uiState.continuing || []).filter(function(x) { return !(x.position_ms > 0) }); visible: items.length > 0 }
            ContentCarousel { title: Strings.t("Mi lista", "A miña lista"); items: backend.uiState.favorites; visible: items.length > 0 && backend.uiState.page === "Home" }
            Row { spacing: Theme.gap; visible: backend.uiState.busy && !backend.uiState.rows.length
                Repeater { model: Theme.skeletonCount; Rectangle { width: Theme.cardWidth; height: Theme.posterHeight; color: Theme.card; radius: Theme.radius; opacity: 0.5 } }
            }
            Repeater { model: backend.uiState.rows; delegate: ContentCarousel { required property var modelData; title: modelData.title; items: modelData.items } }
            ContentCarousel { title: Strings.t("Vistos recientemente", "Vistos recentemente"); subtitle: ""; items: backend.uiState.history; visible: items.length > 0 && backend.uiState.page === "Home" }
            Text { font.family: Theme.font; visible: !backend.uiState.rows.length && !backend.uiState.busy; width: parent.width; text: backend.uiState.tmdbAvailable ? Strings.t("No hay títulos disponibles. Prueba Explorar.", "Non hai títulos dispoñibles. Proba Explorar.") : Strings.t("Tu colección aparecerá aquí. Encuentra películas en Explorar.", "A túa colección aparecerá aquí. Atopa películas en Explorar."); color: Theme.muted; wrapMode: Text.WordWrap; font.pixelSize: Theme.body }
        }
    }
}
