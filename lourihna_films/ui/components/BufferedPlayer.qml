import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import ".."
import "." as Styled

Item {
    id: root; objectName: "bufferedPlayer"
    property url mediaUrl
    property int sessionId: 0
    property string sessionKey: ""
    property string failure: ""
    property real lastPosition: 0
    property real pendingResume: 0
    property bool resumed: false
    property bool completed: false
    property bool playAfterLoad: true
    property string selectedAudioId: ""
    readonly property var audioDevices: audioDevicesMonitor.audioOutputs
    readonly property int selectedAudioIndex: {
        for (var i = 0; i < audioDevices.length; ++i)
            if (String(audioDevices[i].id) === selectedAudioId) return i;
        return -1;
    }
    onAudioDevicesChanged: {
        // A disconnected manual output falls back to the current system default.
        if (selectedAudioId && selectedAudioIndex < 0) selectedAudioId = "";
    }
    MediaDevices { id: audioDevicesMonitor }
    function changeQuality(index) { flush(); playAfterLoad = media.playbackState === MediaPlayer.PlayingState; revealControls(); backend.selectQuality(index) }
    function qualityLabel(source) {
        var names = { mobile: "Móvil", lowest: "Mínima", low: "Baja", sd: "SD", hd: "HD", full: "Full HD", quad: "QHD", ultra: "UHD" };
        return source.height ? source.height + "p" : names[source.quality] || source.quality || "Original"
    }
    property bool controlsVisible: true
    readonly property real frameHeight: picture.sourceRect.height
    readonly property real playbackPosition: media.position
    readonly property int playbackStatus: media.mediaStatus
    readonly property int playbackState: media.playbackState
    readonly property bool editing: Window.window && Window.window.activeFocusItem && Window.window.activeFocusItem.cursorPosition !== undefined
    signal fullscreenRequested()
    signal closed()
    signal failed(int code)
    function clockText(ms) { var s = Math.floor(ms / 1000); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0") }
    function revealControls() { controlsVisible = true; hideControls.restart() }
    function flush() { if (sessionKey && resumed && lastPosition > 0 && !completed) backend.saveProgress(sessionKey, sessionId, lastPosition, media.duration, false) }
    function stop() { flush(); media.stop() }
    function toggle() { revealControls(); if (media.playbackState === MediaPlayer.PlayingState) { flush(); media.pause() } else { completed = false; media.play() } }
    function seek(delta) { revealControls(); if (media.seekable) media.position = Math.max(0, Math.min(media.duration, media.position + delta)) }
    function changeVolume(delta) { revealControls(); backend.setVolume(Math.max(0, Math.min(1, sound.volume + delta)), false) }
    function fail(code) {
        if (failure) return
        flush(); failure = Strings.t("No se pudo reproducir esta fuente.", "Non se puido reproducir esta fonte.")
        startup.stop(); stall.stop(); media.stop()
        var key = sessionKey; var session = sessionId
        Qt.callLater(function() { backend.playbackFailed(key, session, code) })
    }
    function restore() {
        if (resumed) return
        if (media.seekable && pendingResume > 0 && media.duration > pendingResume) media.position = pendingResume
        resumed = true; media.play(); if (!playAfterLoad) { pauseAfterLoad.restart(); startup.stop() }
    }
    MediaPlayer {
        id: media; source: root.mediaUrl; videoOutput: picture
        audioOutput: AudioOutput {
            id: sound
            objectName: "playbackAudioOutput"
            device: root.selectedAudioIndex >= 0 ? root.audioDevices[root.selectedAudioIndex] : audioDevicesMonitor.defaultAudioOutput
            volume: backend.viewState.volume === undefined ? 0.8 : backend.viewState.volume
            muted: backend.viewState.muted || false
        }
        onSourceChanged: {
            root.failure = ""; root.resumed = false; root.completed = false
            root.pendingResume = root.lastPosition || backend.viewState.player.position_ms || 0
            startup.restart(); stall.stop(); pauseAfterLoad.stop()
        }
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia) root.restore()
            if (mediaStatus === MediaPlayer.EndOfMedia) {
                root.completed = true; startup.stop(); stall.stop()
                if (root.sessionKey) backend.saveProgress(root.sessionKey, root.sessionId, duration, duration, true)
                root.revealControls()
            }
        }
        onPositionChanged: function(position) {
            if (root.resumed && position > 0) {
                root.lastPosition = position; startup.stop(); stall.restart()
            }
        }
        onPlaybackStateChanged: { if (playbackState !== MediaPlayer.PlayingState) { stall.stop(); root.flush(); root.revealControls() } else if (!startup.running) stall.restart() }
        onErrorOccurred: function(error, errorString) { backend.mediaDiagnostic(root.sessionKey, error, errorString); root.fail(error) }
    }
    VideoOutput { id: picture; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectFit }
    MouseArea { anchors.fill: parent; hoverEnabled: true; onPositionChanged: root.revealControls(); onClicked: root.toggle(); onDoubleClicked: root.fullscreenRequested() }
    Timer { id: pauseAfterLoad; interval: Theme.qualitySettleMs; onTriggered: media.pause() }
    Timer { id: startup; interval: Theme.mediaStartupMs; onTriggered: root.fail(-1) }
    Timer { id: stall; interval: Theme.mediaStallMs; onTriggered: { if (media.playbackState === MediaPlayer.PlayingState) root.fail(-2) } }
    Timer { interval: Theme.progressSaveMs; repeat: true; running: media.playbackState === MediaPlayer.PlayingState; onTriggered: root.flush() }
    Timer { id: hideControls; interval: Theme.controlHideMs; onTriggered: { if (media.playbackState === MediaPlayer.PlayingState && !controlsHover.hovered && !controls.activeFocus && !audioMenu.visible) root.controlsVisible = false } }
    LoadingIndicator { anchors.centerIn: parent; running: !root.failure && (startup.running || media.mediaStatus === MediaPlayer.StalledMedia); visible: running }
    Rectangle {
        id: controls; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        height: Theme.buttonHeight + Theme.margin; color: Theme.panel
        opacity: root.controlsVisible || media.playbackState !== MediaPlayer.PlayingState ? 1 : 0
        visible: opacity > 0; enabled: visible
        Behavior on opacity { NumberAnimation { duration: Theme.duration } }
        HoverHandler { id: controlsHover; onHoveredChanged: { if (hovered) root.revealControls() } }
        RowLayout {
            anchors.fill: parent; anchors.margins: Theme.gap; spacing: Theme.smallGap
            ActionButton { glyph: media.playbackState === MediaPlayer.PlayingState ? "pause" : "play"; Accessible.name: Strings.t("Pausa o reproducción", "Pausa ou reprodución"); onClicked: root.toggle() }
            Text { font.family: Theme.font; font.pixelSize: Theme.body; text: root.clockText(media.position); color: Theme.text }
            Styled.Slider { Layout.fillWidth: true; from: 0; to: Math.max(1, media.duration); value: media.position; enabled: media.seekable; onMoved: { media.position = value; root.revealControls() } }
            Text { font.family: Theme.font; font.pixelSize: Theme.body; text: root.clockText(media.duration); color: Theme.text }
            ActionButton { glyph: sound.muted ? "mute" : "volume"; Accessible.name: Strings.t("Silenciar", "Silenciar"); onClicked: backend.setVolume(sound.volume, !sound.muted) }
            Styled.Slider { Layout.preferredWidth: root.width < Theme.compactWidth ? 80 : 120; from: 0; to: 1; value: sound.volume; Accessible.name: Strings.t("Volumen", "Volume"); onMoved: backend.setVolume(value, false) }
            ActionButton {
                text: "Audio"
                objectName: "audioOutputButton"
                Accessible.name: "Saída de audio"
                onClicked: { root.revealControls(); audioMenu.open(); }
                Menu {
                    id: audioMenu
                    objectName: "audioOutputMenu"
                    width: Math.min(340, root.width - Theme.gap * 2)
                    MenuItem {
                        text: "Automática · " + audioDevicesMonitor.defaultAudioOutput.description
                        checkable: true
                        checked: !root.selectedAudioId
                        onTriggered: root.selectedAudioId = ""
                    }
                    Instantiator {
                        model: root.audioDevices
                        delegate: MenuItem {
                            required property var modelData
                            text: modelData.description
                            checkable: true
                            checked: root.selectedAudioId === String(modelData.id)
                            onTriggered: root.selectedAudioId = String(modelData.id)
                        }
                        onObjectAdded: function(index, object) { audioMenu.insertItem(index + 1, object); }
                        onObjectRemoved: function(index, object) { audioMenu.removeItem(object); }
                    }
                }
            }
            Styled.ComboBox {
                id: quality; Accessible.name: Strings.t("Calidad", "Calidade")
                model: (backend.viewState.bufferedMedia || {}).sources || []
                textRole: "quality"; currentIndex: (backend.viewState.bufferedMedia || {}).index || 0
                displayText: Strings.t("Calidad: ", "Calidade: ") + (model.length ? root.qualityLabel(model[currentIndex] || {}) : "Original") + (picture.sourceRect.height > 0 ? " · " + Math.round(picture.sourceRect.height) + "p" : "")
                Layout.preferredWidth: 160; visible: model.length > 1
                delegate: ItemDelegate { required property var modelData; width: quality.width; text: root.qualityLabel(modelData) }
                onActivated: root.changeQuality(currentIndex)
            }
            ActionButton { glyph: "fullscreen"; Accessible.name: Strings.t("Pantalla completa", "Pantalla completa"); onClicked: root.fullscreenRequested() }
        }
    }
    Shortcut { sequence: "Space"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: root.toggle() }
    Shortcut { sequence: "Left"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: root.seek(-Theme.seekStepMs) }
    Shortcut { sequence: "Right"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: root.seek(Theme.seekStepMs) }
    Shortcut { sequence: "Up"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: root.changeVolume(Theme.volumeStep) }
    Shortcut { sequence: "Down"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: root.changeVolume(-Theme.volumeStep) }
    Shortcut { sequence: "M"; enabled: root.visible && !root.editing && !audioMenu.visible; onActivated: { root.revealControls(); backend.setVolume(sound.volume, !sound.muted) } }
    Component.onCompleted: { sessionId = backend.viewState.playbackSession || 0; sessionKey = backend.viewState.player.key || ""; pendingResume = backend.viewState.player.position_ms || 0; startup.restart(); media.play(); revealControls() }
    Component.onDestruction: media.stop()
}
