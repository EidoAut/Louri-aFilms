# Louriña Films

Aplicación de escritorio para descubrir cinema, organizar unha colección local e reproducir fontes públicas compatibles. Emprega Python, PySide6/QML, SQLite e Qt Multimedia/WebEngine. Non precisa unha conta propia da aplicación.

![Pantalla principal de Louriña Films](docs/screenshots/home.png)

**Descargas · v0.4.0 (versión previa)**

| Windows · Intel/AMD de 64 bits | Linux · x86_64 | Código fonte |
| --- | --- | --- |
| [Descargar instalador .exe](https://github.com/EidoAut/Louri-aFilms/releases/download/v0.4.0/lourihna-films-0.4.0-windows-x86_64-setup.exe) | [Descargar paquete .tar.gz](https://github.com/EidoAut/Louri-aFilms/releases/download/v0.4.0/lourihna-films-0.4.0-linux-x86_64.tar.gz) | [Descargar fontes .zip](https://github.com/EidoAut/Louri-aFilms/releases/download/v0.4.0/lourihna-films-0.4.0-source.zip) |

[Notas da versión](https://github.com/EidoAut/Louri-aFilms/releases/tag/v0.4.0) · [Sumas SHA-256](https://github.com/EidoAut/Louri-aFilms/releases/download/v0.4.0/SHA256SUMS.txt) · [Requisitos e instalación](#descargas-e-requisitos)

As descargas son públicas e non precisan iniciar sesión en GitHub.

## Funcións

- Busca de vídeos públicos en OK.ru e fontes alternativas de Internet Archive. A dispoñibilidade depende de cada provedor.
- Catálogos opcionais de películas e series con metadatos de TMDB. Unha ficha de TMDB **non garante** que exista un vídeo reproducible.
- Favoritos, historial, progreso, categorías locais, importación de ligazóns e exploración con carga progresiva.
- Reprodutor integrado, formatos e calidades que a fonte expoña publicamente, e reprodutor oficial cando corresponda. Non elimina restricións de acceso nin DRM.
- Tradución local opcional das sinopses mediante modelos descargados cando fan falta. A primeira tradución require conexión e pode tardar.
- Interface en galego ou castelán e benvida co logotipo durante polo menos tres segundos.

![Pantalla de benvida real](docs/screenshots/splash.png)

## Descargas e requisitos

As distribucións publícanse en [GitHub Releases](https://github.com/EidoAut/Louri-aFilms/releases). A versión 0.4.0 publícase como **versión previa**, con paquetes Windows e Linux que superaron as comprobacións descritas nas notas. Consulta as notas da release para distinguir o sistema probado dos requisitos mínimos do framework.

### Windows

1. Abre Releases e escolle a versión máis recente dispoñible.
2. Para equipos Intel/AMD de 64 bits, escolle o instalador `lourihna-films-0.4.0-windows-x86_64-setup.exe` nos anexos da versión 0.4.0.
3. Executa o instalador e segue os pasos. Instálase para o usuario actual, sen requirir permisos de administrador.
4. Abre **Louriña Films** desde o menú Inicio ou o acceso directo e configura TMDB en **Axustes**, se queres utilizar ese catálogo.

A compilación é x86_64, con Python 3.12 e Qt 6.12. O instalador require Windows 10 1809 ou posterior; a validación local realizouse en Windows 11. Non hai unha compilación ARM nativa nin unha certificación independente de todas as versións de Windows. O instalador non está asinado cun certificado comercial.

### Linux

1. Abre Releases e busca `lourihna-films-0.4.0-linux-x86_64.tar.gz`.
2. Escolle este paquete só para unha distribución x86_64 compatible coa base Ubuntu 24.04 e glibc 2.39 ou posterior. Outros escritorios e distribucións poden precisar bibliotecas adicionais.
3. Descomprime o arquivo e entra no directorio `lourihna_films`.
4. Executa `./lourihna_films` directamente ou `sh install.sh` para instalalo no teu directorio persoal e engadir a entrada do menú.
5. Configura TMDB en **Axustes** de maneira opcional.

Utilízase un arquivo portable con instalador por usuario en lugar de AppImage para conservar a estrutura de Qt/WebEngine sen introducir unha dependencia de FUSE. Non hai paquete ARM nin garantía para distribucións con glibc anterior. O workflow comproba o arranque con Xvfb; esa comprobación non substitúe unha proba interactiva en todos os escritorios.

Os anexos automáticos **Source code (zip)** e **Source code (tar.gz)** son código fonte, **non instaladores**. Se unha plataforma non ten un paquete publicado, podes construílo seguindo as instrucións de desenvolvemento; non descargues un paquete doutra arquitectura.

## TMDB

En **Axustes**, o campo «Clave ou token de TMDB» admite:

- **API Read Access Token**: introdúceo sen o prefixo `Bearer`. A aplicación envíao na cabeceira `Authorization: Bearer …`.
- **API Key v3**: introduce a clave de 32 caracteres hexadecimais. A aplicación envíaa no parámetro `api_key`.

Tamén podes configurar `TMDB_TOKEN` ou `TMDB_API_KEY` no contorno; o token ten prioridade. Non é necesario cambiar o método de autenticación. As credenciais gárdanse con DPAPI en Windows; noutros sistemas a interface só as conserva durante a sesión, ou podes empregar variables de contorno. Non compartas ficheiros `.env` con valores reais.

Consulta a [autenticación oficial](https://developer.themoviedb.org/docs/authentication-application) e as [condicións e atribucións de TMDB](https://developer.themoviedb.org/docs/faq). A API de desenvolvemento permite uso non comercial con atribución; un uso comercial require acordar a licenza correspondente con TMDB.

![TMDB](lourihna_films/assets/tmdb.svg)

> This product uses the TMDB API but is not endorsed or certified by TMDB.

As imaxes e os metadatos de terceiros non se relicencian baixo MIT.

## Executar desde as fontes

Require Python 3.12 ou posterior compatible coas dependencias; as comprobacións de distribución usan Python 3.12.

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux: . .venv/bin/activate
python -m pip install -e ".[dev]"
python main.py
```

En Linux tamén se precisa `libpulse0` para Qt Multimedia. Instala as bibliotecas de Qt indicadas no [workflow](.github/workflows/build.yml). A reprodución require un escritorio gráfico e as bibliotecas multimedia do paquete. As descargas e os servizos externos precisan conexión á Internet.

## Datos e migración

O destino principal é `%LOCALAPPDATA%/lourihna_films` en Windows e `$XDG_DATA_HOME/lourihna_films` en Linux, ou `~/.local/share/lourihna_films` se a variable non está definida. `LOURIHNA_FILMS_DATA_DIR` permite escoller un directorio illado.

A primeira apertura copia a biblioteca da identidade anterior mediante unha copia coherente de SQLite. Conserva os orixinais e non substitúe unha base existente no destino. Inclúe preferencias, favoritos, historial, catálogo e as cachés auxiliares dispoñibles. Os detalles da compatibilidade están en [EIDO e migración](docs/EIDO-MIGRATION.md).

## Desenvolvemento e empaquetado

Le [AGENTS.md](AGENTS.md) e a [guía EIDO Python](docs/standards/EIDO_Python_Programming_Style_Guide_v1.0.txt). Os comentarios e contratos técnicos están en inglés.

```sh
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python scripts/verify_ui.py --compact --stress-explore
python scripts/verify_controls.py
python -m PyInstaller --noconfirm lourihna_films.spec
```

Windows: executa `ISCC packaging/windows.iss` con Inno Setup despois de PyInstaller. O instalador queda en `dist/packages/`. Comproba a aplicación con `python scripts/verify_executable.py dist/lourihna_films/lourihna_films.exe`.

Linux: constrúe nun Linux x86_64 compatible, executa a mesma verificación sobre `dist/lourihna_films/lourihna_films` e segue o paso de empaquetado do workflow para incluír `install.sh`. Non se xeran binarios Linux desde Windows por compilación cruzada.

[GitHub Actions](https://github.com/EidoAut/Louri-aFilms/actions) constrúe e verifica cada plataforma con permisos de lectura. A publicación da release realízase despois de revisar os resultados; os workflows non precisan claves persoais de TMDB.

## Licenza e créditos

Código propio baixo [MIT](LICENSE), copyright © 2026 Samuel Seijo Ribeiro. Desenvolvido por EIDO Automation.

O logotipo actual foi facilitado polo titular do proxecto e consérvase sen modificacións neste cambio. Qt/PySide, FFmpeg, Chromium/WebEngine, Inter e as demais dependencias manteñen as súas propias licenzas e avisos en [docs/licenses](docs/licenses/THIRD-PARTY.md). Os modelos de tradución descárganse por separado e non están incluídos na distribución.

As bibliotecas LGPL distribúense como bibliotecas dinámicas substituíbles. As instrucións anteriores permiten reconstruír a aplicación; non se impide depurar modificacións desas bibliotecas. As fontes e os avisos dos compoñentes correspondentes están enlazados no documento de terceiros. MIT non concede dereitos sobre películas, metadatos, marcas nin contidos dos provedores.
