# Louriña Films 0.5.1-rc.1 — candidato Linux para GLIBC 2.31

Esta versión candidata corrixe o erro `GLIBC_2.38 not found` en Ubuntu 20.04. O Python do paquete anterior requiría GLIBC 2.38 e varias bibliotecas de Qt requirían 2.34. Agora Python e as bibliotecas nativas constrúense dentro de Ubuntu 20.04; non se modifica a GLIBC do equipo.

## Cambios

- Compilación Docker con Ubuntu 20.04 fixado por digest, snapshot APT, fontes verificadas por SHA-256 e dependencias Python fixadas con hashes.
- Python 3.12.15, PyInstaller 6.16.0, PySide6 6.8.3 e OpenSSL 3.5.9. Mantense Python 3.12 para respectar o contrato e as API existentes do proxecto.
- Auditoría de todos os ELF do paquete; a compilación falla se precisan GLIBC posterior a 2.31 ou teñen dependencias sen resolver.
- Instalación sen `sudo` en `~/.local/opt/lourinha-films`, acceso directo e icona no menú, actualización que retira ficheiros obsoletos e desinstalación que conserva os datos persoais.
- As bibliotecas gráficas que deben coincidir cos controladores, incluíndo libstdc++, libgcc, GBM e DRM, proceden do sistema. Python, Qt, FFmpeg e OpenSSL inclúense no paquete.
- Consérvanse a marca, a interface, o catálogo, os provedores, os controis multimedia e a identidade dos perfís.

## Instalación

Descarga os dous anexos `LourinhaFilms-linux-x86_64-glibc231.tar.gz` e `LourinhaFilms-linux-x86_64-glibc231.tar.gz.sha256` no mesmo cartafol. Abre un terminal nese cartafol:

```sh
sha256sum -c LourinhaFilms-linux-x86_64-glibc231.tar.gz.sha256
tar -xzf LourinhaFilms-linux-x86_64-glibc231.tar.gz
cd lourinha-films
./install.sh
```

Abre **Louriña Films** desde o menú de aplicacións. Non se precisa instalar Python nin as dependencias Python. As bibliotecas do escritorio necesarias están documentadas no README incluído. A arquitectura admitida é x86_64.

Para actualizar, pecha a aplicación e repite a instalación co novo paquete. Para desinstalar:

```sh
"$HOME/.local/opt/lourinha-films/uninstall.sh"
```

Os datos e as preferencias consérvanse. Unha instalación histórica en `~/.local/opt/lourihna-films` non se elimina automaticamente.

## Alcance da validación

Os resultados exactos de CI, a auditoría e o informe técnico acompañan esta publicación. As probas gráficas usan Xvfb, Mesa por software e unha saída PulseAudio virtual en contedores independentes de Ubuntu. Non equivalen a certificar todas as combinacións de hardware e escritorio.

É unha **prepublicación**, non unha versión estable: a integración TMDB con credenciais reais, o audio físico, HDMI, GPU física e políticas específicas de escritorios Wayland/AppArmor quedan pendentes. O catálogo público, as buscas e a reprodución de OK.ru e a tradución local probáronse por separado. Non se declara compatibilidade con outras distribucións non comprobadas.

O entorno de compilación pode repetirse con `bash scripts/build-linux.sh`. Os informes gardan a data real da compilación; non se promete igualdade byte por byte entre compilacións.

## Resultados verificados e procedencia

| Sistema x86_64 | Resultado |
| --- | --- |
| Ubuntu 20.04 | Compilación Focal e instalación/reprodución/menú/actualización/desinstalación correctos |
| Ubuntu 22.04 | O mesmo paquete supera a proba independente |
| Ubuntu 24.04 | O mesmo paquete supera a proba independente |

[Execución de GitHub Actions](https://github.com/EidoAut/Louri-aFilms/actions/runs/38456598501).
Commit do binario: `b7c13295e1e49bf5cab9454e59aa62f3466b0f2d`, árbore limpa, rama `main`.
Auditoría: **548 ELF, GLIBC máxima 2.30**, dentro do límite 2.31. Python 3.12.15 e PyInstaller 6.16.0.

Superadas 189 probas Linux; unha omítese por ser exclusiva de Windows. Comprobáronse os controis, audio virtual, catálogo público, buscas e reprodución de OK.ru. O paquete exacto de CI tamén superou a tradución local ao galego e castelán. Os modelos descárganse por separado.

Arquivo: `LourinhaFilms-linux-x86_64-glibc231.tar.gz` (315.806.985 bytes).
SHA-256:

```text
9fab1b04f12535d3a4e34c2beaddd12e274b5d1474fd5d312da7e54e7abc6af3
```

[Informe técnico completo](https://github.com/EidoAut/Louri-aFilms/blob/main/docs/LINUX-RELEASE-REPORT-0.5.1-rc.1.md).
