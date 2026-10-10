import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
ScrollView {
    id: page; clip: true; contentWidth: availableWidth
    ColumnLayout {
        x: Theme.margin; width: Math.min(Theme.messageMaxWidth, page.availableWidth - Theme.margin * 2); spacing: Theme.gap
        Item { height: Theme.gap }
        Text { font.family: Theme.font; text: Strings.page("Settings"); color: Theme.text; font.pixelSize: Theme.heading; font.weight: Font.Bold }
        RowLayout {
            Text { font.family: Theme.font; font.pixelSize: Theme.body; text: Strings.t("Idioma de la aplicación", "Idioma da aplicación"); color: Theme.text }
            ComboBox { model: ["Español", "Galego"]; currentIndex: backend.uiState.uiLanguage === "gl" ? 1 : 0; onActivated: backend.savePreferences(currentIndex === 1 ? "gl" : "es", Theme.motion) }
        }
        CheckBox { text: Strings.t("Reducir movimiento", "Reducir movemento"); checked: !Theme.motion; onToggled: backend.savePreferences(backend.uiState.uiLanguage || "es", !checked) }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
        Text { font.family: Theme.font; text: Strings.t("Catálogo de películas y series", "Catálogo de películas e series"); color: Theme.text; font.pixelSize: Theme.heading }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; text: Strings.t("Conecta tu cuenta de TMDB para descubrir títulos. Los vídeos públicos y tu colección funcionan sin ella.", "Conecta a túa conta de TMDB para descubrir títulos. Os vídeos públicos e a túa colección funcionan sen ela."); color: Theme.muted; wrapMode: Text.WordWrap }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; text: Strings.t("Clave o token de TMDB", "Clave ou token de TMDB"); color: Theme.text }
        TextField { id: tmdb; Layout.fillWidth: true; placeholderText: Strings.t("En blanco conserva el valor actual", "En branco conserva o valor actual"); echoMode: TextInput.Password; selectByMouse: true }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; text: Strings.t("Clave de Brave Search (opcional)", "Clave de Brave Search (opcional)"); color: Theme.text }
        TextField { id: brave; Layout.fillWidth: true; echoMode: TextInput.Password; selectByMouse: true }
        RowLayout {
            Text { font.family: Theme.font; font.pixelSize: Theme.body; text: Strings.t("Idioma de las sinopsis", "Idioma das sinopses"); color: Theme.text }
            ComboBox { id: language; model: ["es-ES", "gl-ES", "en-US", "ru-RU", "fr-FR", "de-DE"]; currentIndex: Math.max(0, model.indexOf(backend.uiState.language || "es-ES")); implicitWidth: 140 }
            ActionButton { text: Strings.t("Guardar", "Gardar"); primary: true; onClicked: { backend.saveSettings(tmdb.text, brave.text, language.currentText); tmdb.clear(); brave.clear() } }
        }
        CheckBox { text: Strings.t("Traducir las sinopsis que no estén en mi idioma (gratis)", "Traducir as sinopses que non estean no meu idioma (gratis)"); checked: backend.uiState.translationEnabled; onToggled: backend.setTranslationEnabled(checked) }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; wrapMode: Text.WordWrap; color: Theme.muted; text: Strings.t("Traducción en tu equipo, sin cuenta. La primera vez descarga un modelo de idioma; después funciona sin conexión. Puede tardar y contener errores.", "Tradución no teu equipo, sen conta. A primeira vez descarga un modelo de idioma; despois funciona sen conexión. Pode tardar e conter erros.") }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; text: backend.uiState.credentialSessionOnly ? Strings.t("En este sistema las claves se usan sólo durante esta sesión. Tendrás que introducirlas al volver a abrir la aplicación.", "Neste sistema as claves úsanse só durante esta sesión. Terás que introducilas ao abrir de novo a aplicación.") : Strings.t("Las claves se guardan de forma protegida para tu usuario.", "As claves gárdanse de forma protexida para o teu usuario."); color: Theme.muted; wrapMode: Text.WordWrap }
        Flow { Layout.fillWidth: true; spacing: Theme.smallGap
            ActionButton { text: Strings.t("Obtener clave de TMDB", "Obter clave de TMDB"); onClicked: backend.openExternal("https://www.themoviedb.org/settings/api") }
            ActionButton { text: Strings.t("Obtener clave de Brave", "Obter clave de Brave"); onClicked: backend.openExternal("https://api-dashboard.search.brave.com") }
            ActionButton { text: Strings.t("Eliminar claves", "Eliminar claves"); onClicked: backend.forgetCredentials() }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
        ActionButton { text: Strings.t("Borrar historial de búsqueda y reproducción", "Borrar historial de busca e reprodución"); onClicked: clearDialog.open() }
        RowLayout {
            Image { source: brandLogo; Layout.preferredWidth: 280; Layout.preferredHeight: 116; fillMode: Image.PreserveAspectFit }
            Text { font.family: Theme.font; text: "Louriña Films · 0.4.0"; color: Theme.text; font.pixelSize: Theme.lead }
        }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; text: Strings.t("Reproducción integrada de vídeos públicos. Algunas fuentes pueden no estar disponibles.", "Reprodución integrada de vídeos públicos. Algunhas fontes poden non estar dispoñibles."); color: Theme.muted; wrapMode: Text.WordWrap }
        Text { text: "This product uses the TMDB API but is not endorsed or certified by TMDB."; color: Theme.muted; Layout.fillWidth: true; wrapMode: Text.WordWrap }
        Image { source: "../../assets/tmdb.svg"; Layout.preferredWidth: 110; Layout.preferredHeight: 25; fillMode: Image.PreserveAspectFit }
        Text { font.family: Theme.font; font.pixelSize: Theme.body; Layout.fillWidth: true; text: Strings.t("Este producto usa la API de TMDB, pero no está avalado ni certificado por TMDB.", "Este produto usa a API de TMDB, pero non está avalado nin certificado por TMDB."); color: Theme.muted; wrapMode: Text.WordWrap }
        Item { height: Theme.margin }
    }
    Dialog { id: clearDialog; width: Math.min(480, page.width - Theme.margin * 2); title: Strings.t("¿Borrar el historial?", "Borrar o historial?"); anchors.centerIn: Overlay.overlay; modal: true; standardButtons: Dialog.Ok | Dialog.Cancel; onAccepted: backend.clearHistory(); Label { width: parent.width; wrapMode: Text.WordWrap; text: Strings.t("Tu lista y tus ajustes se conservarán.", "A túa lista e os teus axustes conservaranse.") } }
}
