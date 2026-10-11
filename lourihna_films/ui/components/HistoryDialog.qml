import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: dialog
    objectName: "historyDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(520, parent.width - Theme.gap * 2)
    modal: true
    focus: true
    title: Strings.t("Eliminar historiales", "Eliminar historiais")
    function choose(scope) {
        searches.checked = scope !== "watch";
        viewing.checked = scope !== "search";
        open();
    }
    contentItem: ColumnLayout {
        spacing: Theme.gap
        CheckBox {
            id: searches
            objectName: "clearSearchHistory"
            text: Strings.t("Historial de búsquedas", "Historial de buscas")
        }
        CheckBox {
            id: viewing
            objectName: "clearWatchHistory"
            text: Strings.t("Historial de reproducción", "Historial de reprodución")
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: viewing.checked ? Strings.t("Se eliminarán los vídeos vistos del historial y su progreso guardado, incluida la lista Continuar viendo.", "Eliminaranse os vídeos vistos do historial e o seu progreso gardado, incluída a lista Continuar vendo.") : Strings.t("Se eliminarán las búsquedas recientes.", "Eliminaranse as buscas recentes.")
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: Strings.t("Tus favoritos, colección y ajustes se conservarán. Esta acción no se puede deshacer.", "Os teus favoritos, colección e axustes conservaranse. Esta acción non se pode desfacer.")
        }
        Label {
            visible: backend.viewState.busy
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Agarda a que remate a carga para borrar o historial."
        }
    }
    footer: DialogButtonBox {
        ActionButton {
            text: "Cancelar"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        ActionButton {
            objectName: "confirmClearHistory"
            text: "Eliminar"
            enabled: (searches.checked || viewing.checked) && !backend.viewState.busy
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        onRejected: dialog.reject()
        onAccepted: dialog.accept()
    }
    onAccepted: backend.clearHistory(searches.checked && viewing.checked ? "all" : searches.checked ? "search" : "watch")
}
