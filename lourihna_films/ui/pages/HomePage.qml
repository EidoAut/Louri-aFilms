import QtQuick
import QtQuick.Controls
import ".."
import "../components"

ScrollView {
    id: page
    objectName: "homePage"
    clip: true
    contentWidth: availableWidth
    property int spotlight: 0
    property var featured: backend.viewState.rows.length ? backend.viewState.rows[0].items.slice(0, 5) : []
    readonly property string catalogPage: typeof cinema !== "undefined" ? cinema.browsePage : backend.viewState.page
    Connections {
        target: page.contentItem
        function onContentYChanged() {
            if (typeof cinema !== "undefined")
                cinema.preview.dismiss();
        }
    }
    Column {
        x: Theme.gutter(page.width)
        width: page.availableWidth - Theme.gutter(page.width) * 2
        spacing: Theme.sectionGap
        topPadding: Theme.smallGap
        bottomPadding: Theme.margin
        FeaturedBanner {
            entry: page.featured.length ? page.featured[page.spotlight % page.featured.length] : ({})
        }
        ContentCarousel {
            title: "Continuar vendo"
            items: (backend.viewState.continuing || []).filter(function (x) {
                return (x.position_ms || 0) > 0;
            })
            visible: items.length > 0 && page.catalogPage === "Home"
        }
        ContentCarousel {
            title: "Pendentes"
            items: (backend.viewState.continuing || []).filter(function (x) {
                return !(x.position_ms > 0);
            })
            visible: items.length > 0
        }
        ContentCarousel {
            title: "A miña lista"
            items: backend.viewState.favorites
            visible: items.length > 0 && page.catalogPage === "Home"
        }
        Row {
            spacing: Theme.cardGap
            visible: backend.viewState.busy && !backend.viewState.rows.length
            Repeater {
                model: 3
                Rectangle {
                    width: (page.availableWidth - Theme.gutter(page.width) * 2 - Theme.cardGap * 2) / 3
                    height: width * 9 / 16
                    color: Theme.card
                    radius: Theme.radius
                    opacity: 0.5
                }
            }
        }
        Repeater {
            model: backend.viewState.rows
            delegate: ContentCarousel {
                required property var modelData
                title: modelData.title
                items: modelData.items
                visible: items.length > 0
            }
        }
        ContentCarousel {
            title: "Vistos recentemente"
            items: backend.viewState.history
            visible: items.length > 0 && page.catalogPage === "Home"
        }
        Text {
            visible: !backend.viewState.rows.length && !backend.viewState.busy
            width: parent.width
            text: "A túa colección aparecerá aquí. Atopa películas en Explorar."
            color: Theme.muted
            wrapMode: Text.WordWrap
            font.family: Theme.font
            font.pixelSize: Theme.lead
        }
    }
}
