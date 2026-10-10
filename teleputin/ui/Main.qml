import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "."
ApplicationWindow {
    id: window
    width: Theme.windowWidth; height: Theme.windowHeight; minimumWidth: Theme.minimumWidth; minimumHeight: Theme.minimumHeight
    visible: true; title: "Louriña Films"; color: Theme.background
    flags: Qt.Window | Qt.FramelessWindowHint
    font.family: Theme.font
    palette.window: Theme.background; palette.windowText: Theme.text; palette.base: Theme.surface; palette.text: Theme.text
    palette.button: Theme.card; palette.buttonText: Theme.text; palette.highlight: Theme.selection; palette.highlightedText: Theme.text
    palette.alternateBase: Theme.card; palette.mid: Theme.border; palette.dark: Theme.border
    palette.light: Theme.card; palette.midlight: Theme.card; palette.shadow: Theme.background
    palette.toolTipBase: Theme.card; palette.toolTipText: Theme.text; palette.placeholderText: Theme.muted
    font.pixelSize: Theme.body
    Binding { target: Strings; property: "language"; value: backend.uiState.uiLanguage || "es" }
    Binding { target: Theme; property: "motion"; value: backend.uiState.motion !== false }
    property bool immersive: window.visibility === Window.FullScreen
    property bool heroPage: ["Home", "Movies", "Series", "Documentaries", "Details"].indexOf(backend.uiState.page) >= 0
    property bool playing: backend.uiState.page === "Player"
    Rectangle {
        id: titlebar; width: parent.width; height: window.immersive ? 0 : Theme.titlebarHeight; color: Theme.background; z: 5; visible: !window.immersive
        MouseArea { anchors.fill: parent; onPressed: window.startSystemMove(); onDoubleClicked: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized() }
        Text { font.family: Theme.font; anchors.left: parent.left; anchors.leftMargin: Theme.margin; anchors.verticalCenter: parent.verticalCenter; text: "Louriña Films  /  " + Strings.t("CINE SIN FRONTERAS", "CINEMA SEN FRONTEIRAS"); font.pixelSize: Theme.caption; font.letterSpacing: 1; color: Theme.muted }
        Row { anchors.right: parent.right; height: parent.height
            ActionButton { glyph: "minimize"; Accessible.name: "Minimizar"; implicitWidth: Theme.buttonHeight; implicitHeight: Theme.titlebarHeight; onClicked: window.showMinimized() }
            ActionButton { glyph: "maximize"; Accessible.name: "Maximizar o restaurar"; implicitWidth: Theme.buttonHeight; implicitHeight: Theme.titlebarHeight; onClicked: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized() }
            ActionButton { glyph: "close"; Accessible.name: "Cerrar"; implicitWidth: Theme.buttonHeight; implicitHeight: Theme.titlebarHeight; onClicked: window.close() }
        }
    }
    Loader {
        id: pageLoader; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.top: titlebar.bottom
        anchors.topMargin: window.heroPage || window.playing || window.immersive ? 0 : Theme.navHeight
        source: { var p = backend.uiState.page; if (p === "Explore") return "pages/ExplorePage.qml"; if (p === "Search") return "pages/SearchPage.qml"; if (p === "Details") return "pages/DetailsPage.qml"; if (p === "Player") return "pages/PlayerPage.qml"; if (p === "Settings") return "pages/SettingsPage.qml"; if (p === "My List") return "pages/FavoritesPage.qml"; return "pages/HomePage.qml"; }
        asynchronous: true

    }
    NavigationBar { anchors.top: titlebar.bottom; width: parent.width; backdrop: null; visible: !window.immersive && !window.playing; z: 3 }
    Rectangle {
        anchors.bottom: parent.bottom; anchors.bottomMargin: Theme.gap; anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - Theme.margin * 2, Theme.messageMaxWidth); height: messageText.implicitHeight + Theme.gap * 2
        radius: Theme.radius; color: Theme.panel; border.color: Theme.border; visible: !!backend.uiState.message && !window.immersive; z: 10
        Text { font.family: Theme.font; id: messageText; anchors.left: parent.left; anchors.right: closeMessage.left; anchors.verticalCenter: parent.verticalCenter; anchors.margins: Theme.gap; text: backend.uiState.message; color: Theme.text; wrapMode: Text.WordWrap; font.pixelSize: Theme.body; textFormat: Text.PlainText }
        ActionButton { id: closeMessage; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; glyph: "close"; Accessible.name: "Cerrar"; implicitWidth: Theme.buttonHeight; onClicked: backend.notify("") }
    }
    Rectangle {
        anchors.right: parent.right; anchors.top: titlebar.bottom; anchors.topMargin: Theme.navHeight + Theme.smallGap; anchors.rightMargin: Theme.margin
        width: loadingRow.implicitWidth + Theme.gap * 2; height: Theme.buttonHeight; radius: Theme.radius; color: Theme.panel
        visible: backend.uiState.busy && !window.playing; z: 4
        Row { id: loadingRow; anchors.centerIn: parent; spacing: Theme.smallGap
            LoadingIndicator { running: parent.parent.visible; width: Theme.heading; height: Theme.heading }
            Text { font.family: Theme.font; anchors.verticalCenter: parent.verticalCenter; color: Theme.text; font.pixelSize: Theme.body
                text: backend.uiState.loadingTask === "catalog" ? Strings.t("Cargando ", "Cargando ") + Strings.page(backend.uiState.page) + "…" : backend.uiState.loadingTask === "details" ? Strings.t("Cargando información y sinopsis…", "Cargando información e sinopse…") : backend.uiState.loadingTask === "search" || backend.uiState.loadingTask === "candidates" ? Strings.t("Buscando vídeos…", "Buscando vídeos…") : Strings.t("Actualizando…", "Actualizando…")
            }
        }
    }
    MouseArea { anchors.right: parent.right; anchors.bottom: parent.bottom; width: Theme.gap; height: Theme.gap; cursorShape: Qt.SizeFDiagCursor; visible: !window.immersive; onPressed: window.startSystemResize(Qt.RightEdge | Qt.BottomEdge); z: 20 }
    Shortcut { sequence: "Ctrl+F"; onActivated: backend.navigate("Search") }
}
