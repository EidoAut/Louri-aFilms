pragma Singleton
import QtQuick

QtObject {
    property string language: "gl"
    function t(es, gl) {
        return language === "gl" && gl ? gl : es;
    }
    function message(value) {
        if (language !== "gl")
            return value;
        var messages = {
            "No se pudo completar la acción. Prueba de nuevo.": "Non se puido completar a acción. Téntao de novo.",
            "Algunas fuentes no están disponibles ahora.": "Algunhas fontes non están dispoñibles agora.",
            "Catálogo conectado. Ya puedes explorar películas.": "Catálogo conectado. Xa podes explorar películas.",
            "Elige un archivo de enlaces de menos de 1 MB.": "Escolle un ficheiro de ligazóns de menos de 1 MB.",
            "Guardado en tu colección.": "Gardado na túa colección.",
            "Este enlace no es compatible.": "Esta ligazón non é compatible.",
            "Añadido a pendientes.": "Engadido a pendentes.",
            "Eliminado de pendientes.": "Eliminado de pendentes.",
            "Ajustes guardados.": "Axustes gardados.",
            "Claves guardadas eliminadas.": "Claves gardadas eliminadas.",
            "Historial borrado.": "Historial borrado.",
            "This saved catalog entry is no longer a discovery source. Search its title on OK.ru.": "Esta ficha xa non dispón dunha fonte. Busca o seu título para atopar vídeos."
        };
        return messages[value] || value;
    }
    function page(value) {
        var es = {
            "Trending Movies": "Tendencias",
            "Popular Series": "Series populares",
            "Popular Movies": "Películas populares",
            "Science Fiction": "Ciencia ficción",
            "Horror": "Terror",
            "Home": "Inicio",
            "Movies": "Películas",
            "Series": "Series",
            "Documentaries": "Documentales",
            "Explore": "Explorar",
            "My List": "Mi lista",
            "Search": "Buscar",
            "Settings": "Ajustes",
            "Library": "Biblioteca",
            "Discover": "Vídeos públicos"
        };
        var gl = {
            "Trending Movies": "Tendencias",
            "Popular Series": "Series populares",
            "Popular Movies": "Películas populares",
            "Science Fiction": "Ciencia ficción",
            "Horror": "Terror",
            "Home": "Inicio",
            "Movies": "Películas",
            "Series": "Series",
            "Documentaries": "Documentais",
            "Explore": "Explorar",
            "My List": "A miña lista",
            "Search": "Buscar",
            "Settings": "Axustes",
            "Library": "Biblioteca",
            "Discover": "Vídeos públicos"
        };
        var parts = value.split(" · ");
        var labels = language === "gl" ? gl : es;
        return (labels[parts[0]] || parts[0]) + (parts.length > 1 ? " · " + parts.slice(1).join(" · ") : "");
    }
}
