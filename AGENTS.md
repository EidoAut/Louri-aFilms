# Louriña Films development

Read and follow `docs/standards/EIDO_Python_Programming_Style_Guide_v1.0.txt` before changing owned Python code. Preserve the guide byte for byte. Use Ruff for formatting and lint; module banners contain exactly 76 characters and the signature `Developed by EIDO Automation`.

Visible brand: **Louriña Films**. ASCII display name: **Lourihna Films**. Python package and executable: `lourihna_films`; distribution slug: `lourihna-films`; brand class name: `LourihnaFilms`; brand environment prefix: `LOURIHNA_FILMS`.

Preserve Qt/QML slot, signal and property contracts and external provider schemas. Keep technical documentation in English and user-facing documentation in Galician. Do not change playback or provider behavior during style work. Do not overwrite user data. Historical identity lookups belong only in `lourihna_films/core/compatibility.py`; migrations preserve originals and existing destinations.

Run proportional verification: Ruff, pytest, imports, actual QML, startup/migration edge cases and packaged smoke checks for distribution changes. Distinguish built artifacts from OS-tested artifacts. Never publish tokens, real `.env` files, user databases, logs, caches or screenshots containing private data. Dependencies and third-party assets retain their licenses; MIT covers owned code only.
