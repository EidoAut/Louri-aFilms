# Auditoría TelePutin 0.3.1

Fecha: 10 de octubre de 2026. Proyecto existente modificado directamente, sin reescritura ni cambio de logotipo. Código fuente: carpeta Codigo. Las capturas usan fixtures explícitos de pruebas, no resultados inventados de una búsqueda real.

## Problemas confirmados

El motor nativo estaba restringido a OK.ru y requería una decisión técnica del usuario. Archive dependía del reproductor web. La comprobación global de H264/AAC podía impedir rutas válidas; los códecs disponibles en WebEngine y Qt Multimedia no son equivalentes. El historial conservaba una marca de pendientes, pero no posición real. La salida no limpiaba siempre bufferedMedia. Linux intentaba usar DPAPI. Las fichas y el inicio exponían herramientas y explicaciones técnicas de forma protagonista.

La ficha concreta de Archive `HisNewJobCharlesChaplin-1915`, mostrada en la captura del usuario, no contiene actualmente un archivo de vídeo: sólo metadatos, torrent y miniatura. Se comprobó la respuesta real del API. Esa indisponibilidad no se resuelve instalando códecs. Otra fuente pública de Archive sí reprodujo vídeo y audio.

## Cambios implementados

| Área | Componentes | Resultado |
| --- | --- | --- |
| Reproducción | providers/public_media.py, providers/archive.py, controllers/application_controller.py | Selección automática de hasta tres formatos públicos; alternativa oficial integrada acotada; sin autenticación ni DRM eludidos |
| Controles | ui/components/BufferedPlayer.qml, ui/pages/PlayerPage.qml, Theme.qml | Volumen, silencio, pausa, avance, reanudación, controles ocultables, atajos, restauración de ventana, carga/inicio/interrupción separados |
| Persistencia | database/repositories.py | Posición real, duración, pendientes y terminados diferenciados; sin guardar URLs temporales |
| Descubrimiento | services/candidate_service.py | Candidatos OK.ru y Archive, variantes por episodio, deduplicación y ranking; elección explícita mantiene procedencia |
| Interfaz | Main.qml, FeaturedBanner, HeroArtwork, VideoCard, ContentCarousel, HomePage, DetailsPage, SearchPage, SettingsPage, FavoritesPage | Menos dorado y etiquetas técnicas; formatos coherentes por carrusel, herramientas secundarias, imágenes pequeñas sin ampliación agresiva |
| Idiomas | Strings.qml y pantallas | Español predeterminado, gallego disponible, idioma TMDB separado; algunos avisos del backend heredado siguen en español/inglés |
| Compatibilidad | core/secrets.py, core/config.py, launch.sh, dependencias | Linux conserva claves sólo en memoria durante la sesión; rutas XDG; Qt limitado a ramas con soporte declarado de Windows 10 |
| Diagnósticos | controlador y logging | Tipo y ubicación de excepciones; error multimedia con URLs y tokens redactados; logs rotativos |
| Distribución | TelePutin.spec, docs/licenses | Plugin multimedia y DLL de FFmpeg incluidas, textos de licencia y referencias de fuentes |

La búsqueda pública HTML de OK.ru no tiene un contrato estable de paginación. Se mantienen sus límites y el fallback de búsqueda web; no se promete acceso a todo el catálogo. RareFilmm no es una dependencia del catálogo. TMDB aporta metadatos, no disponibilidad. La asociación vídeo/ficha se conserva sólo al elegir un candidato y guarda método, puntuación y origen; el ranking no prueba identidad ni derechos.

## Evidencia y pruebas

- **137 pruebas pytest aprobadas** (última ejecución: 27,54 s). Cubren las pruebas previas y nuevos casos de formatos Archive, restricciones, duplicados, episodios, claves Linux, avance real, reintentos acotados, sesiones antiguas y preferencias.
- QML real a 1440 × 1000 y a 960 × 640 lógicos con escala 150 % y gallego: **cero errores QML**. Se revisaron capturas de inicio, ficha, búsqueda, ajustes, errores y reproductor. Las miniaturas pequeñas no se usan como fondo ampliado; la imagen panorámica de prueba sí.
- Script de controles con vídeo local de 30 s: reanudación desde 4 s, pausa estable mediante Espacio, avance mediante flecha derecha, volumen/silencio mediante M, pantalla completa, Escape, restauración de maximización, cierre y posición guardada: **aprobado**. No se midió la salida física de altavoces.
- OK.ru `https://ok.ru/video/2116476930726`: **26 fotogramas y 2 buffers de audio decodificados**, calidad low, NoError.
- Archive `https://archive.org/details/Horror_Express`: **15 fotogramas y 1 buffer de audio decodificados**, MP4, NoError.
- Esas pruebas reales confirman arranque/decodificación de las fuentes en ese momento, no visionado completo, disponibilidad permanente ni permisos de distribución.

## Verificación del paquete Windows

PyInstaller 6.22.3 compiló la aplicación con Python 3.12.2 y PySide6 6.12.0. `verify_executable.py` arrancó el ejecutable con PATH sin Python y datos temporales: **aprobado** el arranque sin claves, ciclo WebEngine, avance de vídeo nativo local, integridad SQLite y cierre con log vacío. El fixture local es AVI sin compresión; las pruebas de H264/audio públicos se hicieron con el runtime de desarrollo. No se afirma una película pública completa reproducida por el ejecutable.

Se comprobó que avcodec-63.dll, avformat-63.dll, avutil-61.dll y Qt6Multimedia.dll coinciden por SHA-256 con el runtime que decodificó las fuentes públicas. El paquete contiene ffmpegmediaplugin.dll, el módulo QML QtMultimedia, QtWebEngineProcess.exe y 27 archivos de licencias/notices. FFmpeg identifica su licencia como LGPL 2.1 o posterior. Los avisos de compilación sobre controladores opcionales MySQL/PostgreSQL y assetdownloader no afectan a los componentes SQLite/QML utilizados; las pruebas anteriores verifican el conjunto cargado.

## Capturas antes/después

[Inicio antes](screenshots/before-home.png) · [Inicio después](screenshots/after-home.png)

[Ficha antes](screenshots/before-details.png) · [Ficha después](screenshots/after-details.png)

[Reproductor y controles](screenshots/after-player-controls.png) · [Error recuperable](screenshots/after-unavailable.png) · [Gallego al 150 %](screenshots/after-galician-dpi150.png)

## Límites y plataformas

Windows 11 x64 es el sistema usado. Windows 10 y Linux **no se han ejecutado aquí**: falta una máquina/VM de cada sistema, prueba de audio/gráficos y empaquetado nativo Linux. La documentación de Qt anuncia Windows 10 1809+ en Qt 6.12, última rama con ese soporte; eso no sustituye probar TelePutin. Linux utiliza un flujo de claves por sesión deliberado; no se afirma integración con un llavero persistente. Si se usaba una ubicación Linux antigua, debe trasladarse manualmente la base de datos a la ruta XDG o definir TELEPUTIN_DATA_DIR.

El fallback web puede depender de códecs/consentimiento del proveedor. Si el vídeo está en un iframe ajeno que no permite inspección, el detector de inicio puede agotar el tiempo. El control de posición, volumen y atajos descrito pertenece al reproductor nativo; no se inventa progreso del web. No se garantiza la eliminación de anuncios del proveedor. No hay descarga permanente ni evasión de autenticación, restricciones o DRM.

Los archivos más pequeños MP4 se priorizan en Archive para iniciar con consumo moderado, seguidos de WebM/Ogv; eso no equivale a conocer su bitrate o calidad perceptual. Una coincidencia de título puede ser incorrecta: hay que revisar los candidatos.

Fuentes técnicas: [Archive Metadata](https://archive.org/developers/md-read.html), [Qt Multimedia](https://doc.qt.io/qt-6/qtmultimedia-index.html), [plataformas Qt](https://doc.qt.io/qt-6/supported-platforms.html), [licencias incluidas](licenses/THIRD-PARTY.md).


## Actualización: búsqueda unificada

La pantalla Buscar elimina la selección de proveedor. El controlador usa `services/unified_search.py`: consulta las fuentes públicas registradas, la biblioteca y películas/series TMDB cuando hay credenciales. Mantiene cursores independientes, no vuelve a consultar fuentes agotadas y aísla sus errores. Deduplica por identificador, sin fusionar vídeos distintos sólo por título. La biblioteca conserva títulos locales. Los métodos específicos anteriores siguen disponibles internamente para fichas/importaciones.

Verificación: **141 pruebas aprobadas**, QML compacto sin errores. La consulta real `clan irlandeses 1990` devolvió 20 vídeos de OK.ru; Archive respondió sin coincidencias. No fue necesario seleccionar OK.ru ni introducir credenciales. Las ramas TMDB y paginación se verificaron con pruebas deterministas. Captura: [búsqueda unificada](screenshots/unified-search.png).
