import QtQuick
import QtQuick.Controls
Window {
    width: 640; height: 360
    visible: true
    title: "Louriña Films"
    color: "#0B1113"
    flags: Qt.Window | Qt.FramelessWindowHint
    Image {
        anchors.centerIn: parent
        width: parent.width * 0.76; height: parent.height * 0.55
        source: "../assets/logo.png"
        fillMode: Image.PreserveAspectFit
        asynchronous: true
    }
    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 3
        gradient: Gradient { orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#00B894" }
            GradientStop { position: 1; color: "#007FC3" }
        }
    }
    Text {
        anchors.bottom: closeButton.top; anchors.bottomMargin: 12
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 64; wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        color: "#F5F0E6"; text: startup.errorMessage
    }
    Button {
        id: closeButton
        anchors.bottom: parent.bottom; anchors.bottomMargin: 16
        anchors.horizontalCenter: parent.horizontalCenter
        text: "Cerrar / Pechar"; visible: startup.errorMessage.length > 0
        onClicked: Qt.quit()
    }
    Shortcut { sequence: "Esc"; onActivated: Qt.quit() }
}
