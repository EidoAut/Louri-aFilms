pragma Singleton
import QtQuick
QtObject {
    property string language: "es"
    function t(es, gl) { return language === "gl" && gl ? gl : es }
    function page(value) {
        var es = {"Trending Movies":"Tendencias", "Popular Series":"Series populares", "Popular Movies":"Películas populares", "Science Fiction":"Ciencia ficción", "Horror":"Terror", "Home":"Inicio", "Movies":"Películas", "Series":"Series", "Documentaries":"Documentales", "Explore":"Explorar", "My List":"Mi lista", "Search":"Buscar", "Settings":"Ajustes", "Library":"Biblioteca", "Discover":"Vídeos públicos"}
        var gl = {"Trending Movies":"Tendencias", "Popular Series":"Series populares", "Popular Movies":"Películas populares", "Science Fiction":"Ciencia ficción", "Horror":"Terror", "Home":"Inicio", "Movies":"Películas", "Series":"Series", "Documentaries":"Documentais", "Explore":"Explorar", "My List":"A miña lista", "Search":"Buscar", "Settings":"Axustes", "Library":"Biblioteca", "Discover":"Vídeos públicos"}
        var parts = value.split(" · "); var labels = language === "gl" ? gl : es
        return (labels[parts[0]] || parts[0]) + (parts.length > 1 ? " · " + parts.slice(1).join(" · ") : "")
    }
}
