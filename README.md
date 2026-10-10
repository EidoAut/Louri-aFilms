# Louriña Films 0.3.4

Aplicación de cine en Python/PySide6/QML. Mantiene TMDB, OK.ru, Internet Archive, favoritos, historial y la nueva identidad de Louriña Films. Selecciona un vídeo y pulsa **Reproducir**: la ruta nativa se elige automáticamente; si fallan sus formatos públicos, se intenta el reproductor oficial integrado una sola vez. No guarda películas completas.

En **Explorar**, baja para cargar automáticamente más vídeos. Si una fuente falla, pulsa **Reintentar**; cuando no queden resultados, la carga se detiene.

## Windows portable

Extrae el ZIP completo y abre `TelePutin.exe`. Mantén `_internal` junto al ejecutable. No requiere instalar Python. El paquete se ha comprobado en Windows 11 x64; Windows 10 todavía requiere validación en una máquina real.

## Ejecutar desde el código

Python 3.12 recomendado. En Windows:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

Después puedes utilizar `launch.ps1`. En Linux con sesión gráfica:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
sh launch.sh
```

Qt requiere las bibliotecas del sistema de la distribución (X11/XCB o Wayland, OpenGL y audio). No ejecutes WebEngine como root ni desactives su sandbox. Consulta los requisitos oficiales: https://doc.qt.io/qt-6/linux.html . No se ha construido ni probado un binario Linux en este equipo Windows.

## Catálogo y claves

La aplicación arranca sin claves: Explorar ofrece Archive, la biblioteca local conserva lo descubierto y puedes importar enlaces públicos de OK.ru. TMDB es opcional y aporta el catálogo cinematográfico: en **Ajustes**, introduce tu clave o token personal. Una ficha de TMDB no garantiza que exista un vídeo disponible. Revisa y selecciona los candidatos reales de OK.ru/Archive.

El idioma de interfaz (español/gallego) es independiente del idioma TMDB. En Windows las claves guardadas se protegen con DPAPI. En Linux se conservan **sólo durante la sesión**, sin escribirlas en claro: tendrás que introducirlas de nuevo al abrir la aplicación. Las variables de entorno existentes siguen disponibles.

## Búsqueda unificada

Buscar prioriza OK.ru. Si no devuelve vídeos, consulta las demás fuentes públicas disponibles (actualmente Internet Archive); tu biblioteca sigue accesible. Si TMDB está configurado, incluye películas y series. No tienes que elegir proveedor. Los fallos de una fuente no eliminan los resultados de las demás; «Ver más» sólo consulta las fuentes que anunciaron otra página. Las fichas TMDB conservan su acción de detalles y los vídeos su acción de reproducción.

## Controles

- Espacio: pausa/reproducción. Flechas izquierda/derecha: 10 segundos. Arriba/abajo: volumen. M: silencio.
- Pantalla completa conserva el estado anterior de la ventana. Escape sale de pantalla completa; después vuelve al catálogo.
- Los controles aparecen con ratón o teclado y se ocultan durante la reproducción.
- El motor nativo guarda posición cada cinco segundos y al pausar/salir. **Continuar viendo**, **Pendientes** y **Terminada** son estados distintos. El reproductor web no inventa posiciones.
- Herramientas de organización, página original y actualización están en menús secundarios.

## Datos

Windows: `%LOCALAPPDATA%/TelePutin`. Linux: `$XDG_DATA_HOME/TelePutin` o `~/.local/share/TelePutin`. `TELEPUTIN_DATA_DIR` permite usar otra carpeta. SQLite conserva favoritos, categorías, títulos locales e historial. Las URLs temporales de reproducción no se guardan en la biblioteca. Logs rotativos: `teleputin.log`; no compartas tu base de datos personal.

## Pruebas y empaquetado

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/verify_ui.py --compact
python scripts/verify_controls.py
python scripts/verify_buffered_player.py https://ok.ru/video/2116476930726 --require-audio
python scripts/verify_buffered_player.py https://archive.org/details/Horror_Express --require-audio
python -m PyInstaller --noconfirm TelePutin.spec
python scripts/verify_executable.py dist/TelePutin/TelePutin.exe
```

Usa el Python del entorno virtual; en Linux el ejecutable es `dist/TelePutin/TelePutin`, sin `.exe`. Compila en cada sistema de destino: PyInstaller no genera binarios Linux desde Windows. PySide está limitado a `<6.13`, ya que Qt 6.12 es la última rama que anuncia Windows 10: https://doc.qt.io/qt-6/supported-platforms.html .

Consulta [cambios actuales](docs/CHANGES-0.3.2.md), [auditoría y limitaciones](docs/AUDIT-0.3.1.md), [reproducción](docs/BUFFERED-PLAYBACK.md) y [licencias](docs/licenses/THIRD-PARTY.md). Los scripts de verificación usan datos aislados; sus títulos ficticios sólo son fixtures de pruebas, nunca resultados del catálogo.


## Traducción gratuita y calidad de vídeo

En Ajustes, elige el idioma de las sinopsis y guarda. Si una ficha TMDB no ofrece sinopsis en ese idioma, al abrirla se obtiene la versión inglesa y se traduce en tu equipo. No necesita cuenta ni API de pago. La primera vez descarga el modelo Argos correspondiente; español y gallego ya están preparados en este equipo. Los modelos no se incluyen en los ZIP y se descargan al necesitarlos en otro equipo. Idiomas soportados: español, gallego, francés, alemán y ruso, partiendo del inglés. La traducción se etiqueta como automática, conserva el original y se guarda en caché. Puedes desactivarla en Ajustes. Si no hay sinopsis inglesa o falla el modelo, se conserva la descripción disponible.

El reproductor ofrece un selector de calidad cuando el vídeo publica varias variantes. Sólo muestra las disponibles. OK.ru suele dar etiquetas Móvil/Baja/SD/HD, sin resolución numérica: la altura real se muestra al reproducir la variante. No se anuncian 320p/720p/1080p sin conocer las dimensiones. Cambiar de variante conserva posición y pausa cuando la fuente admite desplazamiento. El reproductor oficial web conserva sus propios controles de calidad.


## Navegación 0.3.3

Los catálogos ya visitados se reutilizan durante cinco minutos para evitar recargas al cambiar de menú. «Opciones → Actualizar catálogo» fuerza la actualización. Repetir un clic en la sección que está cargando no reinicia la petición. El indicador muestra qué operación está pendiente. Las tarjetas parten también títulos sin espacios, limitan el texto a dos líneas y ajustan la resolución de sus imágenes al tamaño visible.
