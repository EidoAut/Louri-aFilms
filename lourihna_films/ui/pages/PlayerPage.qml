import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import ".."
import "../components"
import "../components/PlayerNavigation.js" as Navigation

Item {
    id: player; objectName: "playerPage"
    property bool fullscreen: false
    property int previousVisibility: Window.Windowed
    property string failure: ""
    property bool webStarted: false
    readonly property string playerUrl: backend.viewState.player.embed_url || "about:blank"
    readonly property bool bufferedActive: !!(backend.viewState.bufferedMedia && backend.viewState.bufferedMedia.url)
    readonly property bool webActive: !bufferedActive && backend.viewState.playbackPhase === "web" && !failure
    property bool headerVisible: true
    function toggleFullscreen() {
        if (!fullscreen) { previousVisibility = Window.window.visibility; fullscreen = true; Window.window.showFullScreen() }
        else { fullscreen = false; Window.window.visibility = previousVisibility }
    }
    function leave() { if (native.item) native.item.stop(); if (fullscreen) toggleFullscreen(); backend.backFromPlayer() }
    function retry() { failure = ""; webStarted = false; backend.playBuffered() }
    onWebActiveChanged: { if (webActive) { webStarted = false; playbackMonitor.lastTime = -1; pageLoad.restart() } else { pageLoad.stop(); webStart.stop(); webStall.stop() } }
    onPlayerUrlChanged: { failure = ""; webStarted = false }
    Connections { target: player.Window.window; function onClosing(close) { if (native.item) native.item.stop() } }
    Rectangle { anchors.fill: parent; color: Theme.background }
    Loader {
        id: native; anchors.fill: parent; active: player.bufferedActive
        sourceComponent: BufferedPlayer {
            mediaUrl: backend.viewState.bufferedMedia ? backend.viewState.bufferedMedia.url || "" : ""
            onFullscreenRequested: player.toggleFullscreen()
            
            onControlsVisibleChanged: player.headerVisible = controlsVisible
        }
    }
    Loader {
        id: browser; anchors.fill: parent; active: player.webActive
        sourceComponent: WebEngineView {
            id: web; url: player.playerUrl; backgroundColor: Theme.background
            property string blockedNavigation: ""
            settings.fullScreenSupportEnabled: true; settings.playbackRequiresUserGesture: true
            settings.javascriptCanOpenWindows: false; settings.pluginsEnabled: false; settings.hyperlinkAuditingEnabled: false
            profile: WebEngineProfile { offTheRecord: true; onDownloadRequested: function(download) { download.cancel() } }
            onPermissionRequested: function(permission) { permission.deny() }
            onNewWindowRequested: function(request) {}
            onNavigationRequested: function(request) { if (request.isMainFrame && !Navigation.allowsNavigation(request.url, player.playerUrl, false)) { blockedNavigation = String(request.url); request.reject() } }
            onFullScreenRequested: function(request) { request.accept(); if (request.toggleOn !== player.fullscreen) player.toggleFullscreen() }
            onLoadingChanged: function(info) {
                if (info.status === WebEngineView.LoadSucceededStatus) { pageLoad.stop(); webStart.restart() }
                if (info.status === WebEngineView.LoadFailedStatus && String(info.url) !== blockedNavigation) player.failure = Strings.t("No se pudo abrir el vídeo. Prueba otra fuente.", "Non se puido abrir o vídeo. Proba outra fonte.")
            }
            onRenderProcessTerminated: function(status, code) { player.failure = Strings.t("El reproductor se ha cerrado. Inténtalo de nuevo.", "O reprodutor pechouse. Téntao de novo.") }
        }
    }
    Timer { id: pageLoad; interval: Theme.mediaStartupMs; onTriggered: player.failure = Strings.t("La fuente no responde. Prueba de nuevo.", "A fonte non responde. Proba de novo.") }
    Timer { id: webStart; interval: Theme.mediaStartupMs; onTriggered: player.failure = Strings.t("No se ha podido iniciar el vídeo. Prueba otra fuente.", "Non se puido iniciar o vídeo. Proba outra fonte.") }
    Timer { id: webStall; interval: Theme.mediaStallMs; onTriggered: player.failure = Strings.t("Se ha interrumpido el vídeo. Prueba de nuevo.", "Interrompeuse o vídeo. Proba de novo.") }
    Timer {
        id: playbackMonitor
        interval: 1000; repeat: true; running: player.webActive && !!browser.item
        property real lastTime: -1
        onTriggered: { var session = backend.viewState.playbackSession; browser.item.runJavaScript("JSON.stringify(Array.from(document.querySelectorAll('video')).map(v=>({time:v.currentTime,paused:v.paused,error:!!v.error})))", function(raw) {
            if (!player.webActive || session !== backend.viewState.playbackSession) return
            var videos = []; try { videos = JSON.parse(raw) } catch (e) {}
            for (var i = 0; i < videos.length; i++) {
                if (videos[i].error) { player.failure = Strings.t("No se pudo reproducir este vídeo.", "Non se puido reproducir este vídeo."); return }
                if (videos[i].time > lastTime && videos[i].time > 0) { player.webStarted = true; webStart.stop(); webStall.restart() }
                // Compare consecutive samples so rewinding does not look like a stall.
                lastTime = videos[i].time
                if (videos[i].paused) webStall.stop()
            }
        }) }
    }
    Rectangle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: Theme.navHeight
        color: Theme.glass; visible: player.headerVisible || !player.bufferedActive
        RowLayout {
            anchors.fill: parent; anchors.margins: Theme.gap
            ActionButton { glyph: "back"; Accessible.name: Strings.t("Volver", "Volver"); onClicked: player.leave() }
            Text { font.family: Theme.font; Layout.fillWidth: true; text: (backend.viewState.player.catalog || {}).title || backend.viewState.player.title || ""; color: Theme.text; font.pixelSize: Theme.lead; elide: Text.ElideRight; textFormat: Text.PlainText }
            ActionButton { text: Strings.t("Opciones", "Opcións"); onClicked: actions.open()
                Menu { id: actions
                    MenuItem { text: Strings.t("Añadir a pendientes", "Engadir a pendentes"); onTriggered: backend.keepWatching(true) }
                    MenuItem { text: Strings.t("Marcar como terminada", "Marcar como rematada"); onTriggered: { if (native.item) native.item.stop(); backend.finishPlayback() } }
                    MenuItem { text: Strings.t("Página original", "Páxina orixinal"); onTriggered: backend.openExternal(backend.viewState.player.original_url || "") }
                    MenuItem { text: Strings.t("Pantalla completa", "Pantalla completa"); onTriggered: player.toggleFullscreen() }
                }
            }
        }
    }
    Column {
        anchors.centerIn: parent; width: Math.min(parent.width - Theme.margin * 2, Theme.textMaxWidth); spacing: Theme.gap
        visible: !!player.failure || backend.viewState.playbackPhase === "error"
        Text { font.family: Theme.font; width: parent.width; text: player.failure || Strings.t("Este vídeo no está disponible. Prueba otra fuente.", "Este vídeo non está dispoñible. Proba outra fonte."); color: Theme.text; font.pixelSize: Theme.heading; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }
        Row { anchors.horizontalCenter: parent.horizontalCenter; spacing: Theme.gap
            ActionButton { text: Strings.t("Reintentar", "Tentar de novo"); primary: true; onClicked: player.retry() }
            ActionButton { text: Strings.t("Volver", "Volver"); onClicked: player.leave() }
        }
    }
    LoadingIndicator { anchors.centerIn: parent; running: backend.viewState.playbackPhase === "loading" || (player.webActive && !player.webStarted); visible: running && !player.failure }
    Shortcut { sequence: "Escape"; onActivated: { if (player.fullscreen) player.toggleFullscreen(); else player.leave() } }
    Component.onDestruction: { if (player.fullscreen) Window.window.visibility = player.previousVisibility }
}
