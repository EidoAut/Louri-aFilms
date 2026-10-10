# LourihnaFilms 0.3.2

## Cambios

- Traducción gratuita local de sinopsis TMDB ausentes en el idioma elegido. Se usa la sinopsis inglesa como fuente y modelos públicos Argos, ejecutados con CTranslate2 y SentencePiece. Sin cuenta, API de pago ni envío de la sinopsis a un traductor remoto. Descarga inicial de modelos y caché SQLite; conserva original e identifica el resultado automático. No retraduce sinopsis localizadas que ya existen. Traducción aplicada al abrir la ficha, no masivamente a todos los resultados del catálogo.
- Botones de catálogo con texto: Opciones, Más opciones, Añadir vídeos, Anterior, Siguiente, Mi lista y Ver. Los controles del reproductor mantienen símbolos convencionales.
- Selector de variantes nativas. Se conservan todas las variantes válidas publicadas por OK.ru y hasta 20 archivos públicos de Archive. Los reintentos automáticos siguen limitados a tres y una alternativa web. Selección manual preserva posición y pausa; se prepara un fotograma antes de volver a pausar para evitar una pantalla negra.
- OK.ru se consulta primero tanto en búsqueda unificada como en candidatos de ficha. Ante cero resultados o fallo se consultan las demás fuentes disponibles. Actualmente la otra fuente de vídeos es Internet Archive; TMDB sigue siendo metadatos y la biblioteca conserva lo guardado. Esto no implica asociación, afiliación ni garantía de disponibilidad del proveedor.

## Verificación

147 pruebas unitarias aprobadas. Traducciones reales inglés→español e inglés→gallego con modelos descargados: resultados no vacíos y comprensibles, ejecutados localmente. Se comprobó que el cambio de calidad conserva posición, pausa e imagen con dos archivos locales, además de los controles existentes. QML compacto sin errores.

Los modelos públicos están en https://github.com/argosopentech/argospm-index ; el motor está documentado en https://opennmt.net/CTranslate2/ . La resolución sólo se muestra cuando es conocida por el vídeo decodificado; las etiquetas del proveedor no se convierten arbitrariamente a números. Las calidades, idiomas y derechos disponibles dependen de cada fuente. La traducción automática puede contener errores. No se verificó Windows 10 ni Linux en este equipo Windows 11.


Capturas: [calidad](screenshots/quality-selector.png), [botones con texto](screenshots/named-controls.png), [ajustes de traducción](screenshots/translation-settings.png).

Prueba reproducible del motor empaquetado: `python scripts/verify_translation.py <lourihna_films.exe> <carpeta-de-datos>/translation-models`. Los modelos se instalan al traducir por primera vez. El modelo español utilizado es en_es 1.0 y el gallego en_gl 1.9. Estos modelos descargados quedan en los datos del usuario, no en los ZIP.

El ejecutable portable pasó traducción local real en español/gallego con PATH sin Python, además de arranque, vídeo nativo, ciclo WebEngine, SQLite y cierre limpio.
