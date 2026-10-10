pragma Singleton
import QtQuick
QtObject {
    property bool motion: true
    readonly property color background: "#0B1012"
    readonly property color red: "#27B99A"
    readonly property color selected: "#173C50"
    readonly property color gold: "#65B5F3"
    readonly property color text: "#F3F0E8"
    readonly property color surface: "#151D20"
    readonly property color card: "#202B2F"
    readonly property color muted: "#A3AFB3"
    readonly property color border: "#2B383D"
    readonly property color glass: "#0B1012"
    readonly property color panel: "#151D20"
    readonly property color shadow: "#00000000"
    readonly property color hover: "#42CCAF"
    readonly property color transparent: "transparent"
    readonly property color heroShade: "#E60B1012"
    readonly property int margin: 48
    readonly property int gap: 16
    readonly property int smallGap: 8
    readonly property int radius: 8
    readonly property int buttonRadius: 6
    readonly property int duration: motion ? 180 : 0
    readonly property int pageDuration: motion ? 320 : 0
    readonly property FontLoader interfaceFont: FontLoader { source: "../assets/fonts/Inter.ttf" }
    readonly property string font: interfaceFont.status === FontLoader.Ready ? interfaceFont.name : "sans-serif"
    readonly property color accent: "#27B99A"
    readonly property color selection: "#287CC1"
    readonly property color accentText: "#0B1012"
    readonly property color warning: "#E0AE65"
    readonly property color error: "#EF8D85"
    readonly property int iconSize: 20
    readonly property int menuWidth: 280
    readonly property url symbol: Qt.resolvedUrl("../assets/brand/lourina-symbol.png")
    readonly property int smallButtonHeight: 32
    readonly property int controlHideMs: 3000
    readonly property int mediaStartupMs: 30000
    readonly property int mediaStallMs: 20000
    readonly property int progressSaveMs: 5000
    readonly property int seekStepMs: 10000
    readonly property real volumeStep: 0.05
    readonly property int caption: 12
    readonly property int body: 14
    readonly property int lead: 17
    readonly property int heading: 28
    readonly property int display: 52
    readonly property int titlebarHeight: 30
    readonly property int navHeight: 88
    readonly property int buttonHeight: 44
    readonly property int cardWidth: 202
    readonly property int qualitySettleMs: 150
    readonly property int cardHeight: 368
    readonly property int posterHeight: 286
    readonly property int videoWidth: 302
    readonly property int videoHeight: 252
    readonly property int thumbnailHeight: 170
    readonly property real heroPortraitWidthRatio: 0.46
    readonly property int heroMin: 320
    readonly property int heroMax: 400
    readonly property real heroRatio: 0.32
    readonly property int heroArtworkMinWidth: 960
    readonly property int heroArtworkMinHeight: 480
    readonly property real heroArtworkMinAspect: 1.4
    readonly property real heroArtworkMaxUpscale: 1.6
    readonly property int heroPreviewMaxWidth: 360
    readonly property int heroPreviewMaxHeight: 300
    readonly property real heroPreviewWidthRatio: 0.28
    readonly property color heroFallbackTint: "#0B1012"
    readonly property real hoverScale: 1.0
    readonly property real navBlur: 0.75
    readonly property int blurMax: 32
    readonly property int shadowOffset: 8
    readonly property real shadowBlur: 0.7
    readonly property real scrimStop: 0.65
    readonly property int windowWidth: 1440
    readonly property int windowHeight: 900
    readonly property int minimumWidth: 960
    readonly property int minimumHeight: 640
    readonly property int compactWidth: 1150
    readonly property int textMaxWidth: 650
    readonly property int messageMaxWidth: 950
    readonly property int skeletonCount: 6
    readonly property int episodeImageWidth: 170
    readonly property int episodeImageHeight: 96
}
