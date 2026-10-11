import QtQuick
import ".."
import "Cinema.js" as Cinema

Item {
    id: banner
    objectName: "featuredBanner"
    property var entry: ({})
    property bool hasEntry: !!entry.title
    readonly property var progress: Cinema.progress(entry, backend.viewState.history || [])
    width: parent.width
    height: Math.min(Theme.heroMax, Math.max(Theme.heroMin, width * Theme.heroRatio), Window.window ? Window.window.height * 0.57 : Theme.heroMax)
    HeroArtwork {
        anchors.fill: parent
        entry: banner.entry
        hero: true
        radius: Theme.heroRadius
    }
    Rectangle {
        anchors.fill: parent
        radius: Theme.heroRadius
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop {
                position: 0
                color: Theme.heroShade
            }
            GradientStop {
                position: 0.7
                color: Theme.transparent
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        radius: Theme.heroRadius
        gradient: Gradient {
            GradientStop {
                position: 0.15
                color: Theme.transparent
            }
            GradientStop {
                position: 1
                color: Theme.heroShade
            }
        }
    }
    Column {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: banner.width < Theme.narrowWidth ? Theme.gap * 1.5 : Theme.margin
        width: Math.min(Theme.textMaxWidth, parent.width - anchors.margins * 2)
        spacing: Theme.gap
        Text {
            font.family: Theme.font
            text: "LOURIÑA FILMS  /  EN PRIMEIRO PLANO"
            color: Theme.accent
            font.pixelSize: Theme.caption
            font.letterSpacing: 2
        }
        Text {
            width: parent.width
            text: banner.hasEntry ? Cinema.title(entry) : "A túa próxima historia\ncomeza aquí."
            font.family: Theme.font
            font.pixelSize: banner.width < Theme.narrowWidth ? Theme.compactDisplay : Theme.display
            font.weight: Font.Bold
            color: Theme.text
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
            textFormat: Text.PlainText
        }
        Text {
            visible: banner.hasEntry
            width: parent.width
            text: Cinema.metadata(entry)
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.body
            elide: Text.ElideRight
        }
        Text {
            width: parent.width
            text: banner.hasEntry ? (Cinema.visual(entry).overview || entry.description || "") : "Descubre cinema, garda as túas películas e retoma cada historia."
            visible: !!text
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.lead
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            textFormat: Text.PlainText
            lineHeight: 1.2
        }
        Flow {
            width: parent.width
            spacing: Theme.smallGap
            ActionButton {
                id: heroPrimary
                primary: true
                glyph: banner.hasEntry && entry.kind === "video" ? "play" : "search"
                text: !banner.hasEntry ? "Explorar cinema" : entry.kind === "video" ? (Cinema.resumable(banner.progress) ? "Continuar" : "Reproducir") : "Ver fontes"
                onClicked: !banner.hasEntry ? backend.navigate("Explore") : entry.kind === "video" ? backend.play(entry) : cinema.openDetails(entry, heroPrimary)
            }
            ActionButton {
                id: heroMore
                objectName: "heroDetails"
                visible: banner.hasEntry
                text: "Máis información"
                glyph: "info"
                onClicked: cinema.openDetails(entry, heroMore)
            }
        }
    }
}
