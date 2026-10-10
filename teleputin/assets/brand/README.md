# Louriña Films brand assets

- `lourina-original.png`: exact user-supplied original, retained unchanged.
- `lourina-dark.png`: raster cleanup for the dark application header and About section. Also installed at the existing `../logo.png` path.
- `lourina-symbol.png`: standalone raster symbol on a dark background.
- `lourina.ico`: Windows icon with 16, 24, 32, 48, 64, 128 and 256 px entries; the runtime-compatible path remains `../teleputin.ico`.

The supplied alpha edges contain white/cyan debris. Transparent restoration attempts were rejected because they retained artifacts. The delivered display variants use a dark background and are not vector files or pixel-identical restorations. The original is preserved for replacement by an authoritative clean master. No tracing-to-SVG claim is made.

Tool: built-in image_gen. Full-logo restoration prompt: Restore the exact supplied Louriña FILMS logo on #0B1012, remove white speckles and cyan fringes, retain Celtic ribbon geometry, original serif letterforms, swashes, ñ and colors; no new logo, shadow or outline. Symbol prompt: extract the existing symbol, retain its proportions and film perforations, remove lettering, center on #0B1012 with padding.

UI icons in `../icons` are original simple SVG line icons. The interface font is Inter, bundled unchanged with its SIL Open Font License in `../fonts/OFL-Inter.txt`. Source: https://github.com/google/fonts/tree/main/ofl/inter
