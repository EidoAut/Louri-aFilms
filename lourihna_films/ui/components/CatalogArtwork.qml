import QtQuick
import ".."

Item {
    id: root
    property var entry: ({})
    property real radius: Theme.radius
    property bool hero: false
    property color surroundColor: Theme.background
    readonly property var visual: entry.catalog || entry
    readonly property string sourceKey: [visual.backdrop || "", entry.backdrop || "", visual.still || "", entry.thumbnail_url || "", visual.poster || "", entry.poster || ""].join("|")
    readonly property var sources: sourceKey.split("|").filter(function (value, index, values) {
        return value && values.indexOf(value) === index;
    })
    property int sourceIndex: 0
    property bool ready: false
    property bool panoramic: false
    onSourceKeyChanged: sourceIndex = 0
    Item {
        id: content
        anchors.fill: parent
        clip: true
        Rectangle {
            anchors.fill: parent
            color: Theme.surface
        }
        Image {
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.22, 100)
            height: width
            source: Theme.symbol
            fillMode: Image.PreserveAspectFit
            opacity: 0.35
            visible: !root.ready
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop {
                    position: 0
                    color: Theme.selected
                }
                GradientStop {
                    position: 1
                    color: Theme.surface
                }
            }
            visible: root.ready && !root.panoramic
        }
        Image {
            id: artwork
            width: root.hero && !root.panoramic ? parent.width * Theme.heroPortraitWidthRatio : parent.width
            height: parent.height
            anchors.right: parent.right
            source: root.sources[root.sourceIndex] || ""
            sourceSize.width: root.hero ? 1920 : (Screen.devicePixelRatio > 1 ? 800 : 512)
            asynchronous: true
            cache: true
            fillMode: root.panoramic ? Image.PreserveAspectCrop : Image.PreserveAspectFit
            opacity: root.ready ? 1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: Theme.duration
                }
            }
            onSourceChanged: root.ready = false
            onStatusChanged: {
                if (status === Image.Ready) {
                    root.panoramic = sourceSize.width >= sourceSize.height * Theme.heroArtworkMinAspect;
                    root.ready = true;
                } else if (status === Image.Error && root.sourceIndex + 1 < root.sources.length)
                    root.sourceIndex++;
            }
        }
    }
    // Four tiny textures avoid repainting/uploading an image-sized Canvas.
    Repeater {
        model: 4
        delegate: Canvas {
            id: corner
            required property int index
            width: root.radius
            height: root.radius
            x: index === 1 || index === 2 ? root.width - width : 0
            y: index >= 2 ? root.height - height : 0
            rotation: index * 90
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: root
                function onSurroundColorChanged() {
                    corner.requestPaint();
                }
            }
            onPaint: {
                var c = getContext("2d"), r = width;
                c.clearRect(0, 0, r, r);
                c.fillStyle = root.surroundColor;
                c.beginPath();
                c.moveTo(0, 0);
                c.lineTo(r, 0);
                c.quadraticCurveTo(0, 0, 0, r);
                c.closePath();
                c.fill();
            }
        }
    }
}
