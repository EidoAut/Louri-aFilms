import QtQuick
import ".."
Item {
    id: banner
    property var entry: ({})
    property bool hasEntry: !!entry.title
    readonly property bool saved: hasEntry && backend.uiState.favorites.some(function(x) { return x.key === banner.entry.key })
    width: parent.width; height: Math.max(heroVisual.wideArtwork ? Math.min(Theme.heroMax, width * Theme.heroRatio) : Theme.heroMin, heroCopy.implicitHeight + Theme.navHeight + Theme.gap * 2)
    HeroArtwork { id: heroVisual; anchors.fill: parent; entry: banner.hasEntry ? banner.entry : ({}) }
    Image { visible: !banner.hasEntry; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; anchors.rightMargin: Theme.margin * 2; width: parent.width * 0.32; height: width; source: brandLogo; fillMode: Image.PreserveAspectFit; opacity: 0.65 }
    Rectangle { visible: heroVisual.wideArtwork; anchors.fill: parent; gradient: Gradient { orientation: Gradient.Horizontal; GradientStop { position: 0; color: Theme.background } GradientStop { position: Theme.scrimStop; color: Theme.heroShade } GradientStop { position: 1; color: Theme.transparent } } }
    Rectangle { visible: heroVisual.wideArtwork; anchors.fill: parent; gradient: Gradient { GradientStop { position: 0.4; color: Theme.transparent } GradientStop { position: 1; color: Theme.background } } }
    Column {
        id: heroCopy
        anchors.left: parent.left; anchors.leftMargin: Theme.margin; anchors.bottom: parent.bottom; anchors.bottomMargin: Theme.gap * 2
        width: Math.min(Theme.textMaxWidth, parent.width * 0.65); spacing: Theme.gap
        Text { font.family: Theme.font; text: banner.hasEntry ? (entry.kind === "video" ? Strings.t("Una historia por descubrir", "Unha historia por descubrir") : Strings.t("En primer plano", "En primeiro plano")) : "Louriña Films"; color: Theme.text; font.pixelSize: Theme.caption; font.letterSpacing: 0.5 }
        Text { font.family: Theme.font; width: parent.width; text: banner.hasEntry ? entry.title : Strings.t("Tu próxima historia\nempieza aquí.", "A túa próxima historia\ncomeza aquí."); color: Theme.text; font.pixelSize: banner.width < Theme.compactWidth ? Theme.display * 0.72 : Theme.display; font.weight: Font.DemiBold; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight; textFormat: Text.PlainText }
        Text { font.family: Theme.font; visible: banner.hasEntry; text: [entry.year || "", entry.rating ? "TMDB " + Number(entry.rating).toFixed(1) : "", entry.kind === "tv" ? Strings.t("Serie", "Serie") : entry.kind === "movie" ? Strings.t("Película", "Película") : Strings.t("Vídeo", "Vídeo")].filter(Boolean).join("   ·   "); color: Theme.text; font.pixelSize: Theme.body }
        Text { font.family: Theme.font; width: parent.width; text: banner.hasEntry ? (entry.overview || entry.description || Strings.t("Descubre esta película y elige dónde verla.", "Descubre esta película e escolle onde vela.")) : Strings.t("Explora vídeos públicos o conecta tu catálogo en Ajustes.", "Explora vídeos públicos ou conecta o teu catálogo en Axustes."); color: Theme.text; font.pixelSize: Theme.lead; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight; lineHeight: 1.3; textFormat: Text.PlainText }
        Flow { width: parent.width; spacing: Theme.smallGap
            ActionButton { primary: true; text: banner.hasEntry ? (entry.kind === "video" ? Strings.t("Reproducir", "Reproducir") : Strings.t("Ver detalles", "Ver detalles")) : Strings.t("Explorar películas", "Explorar películas"); onClicked: banner.hasEntry ? (entry.kind === "video" ? backend.play(entry) : backend.select(entry)) : backend.navigate("Explore") }
            ActionButton { text: banner.hasEntry ? (banner.saved ? Strings.t("Quitar de mi lista", "Quitar da miña lista") : Strings.t("Añadir a mi lista", "Engadir á miña lista")) : Strings.t("Ajustes", "Axustes"); onClicked: banner.hasEntry ? backend.favorite(entry) : backend.navigate("Settings") }
        }
        Text { font.family: Theme.font; text: banner.hasEntry && entry.kind !== "video" ? Strings.t("Consulta las fuentes disponibles en la ficha", "Consulta as fontes dispoñibles na ficha") : ""; color: Theme.muted; font.pixelSize: Theme.caption }
    }
}
