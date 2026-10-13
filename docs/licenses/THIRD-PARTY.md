# Bundled third-party components

## Linux GLIBC 2.31 profile

The descriptions below record the earlier Windows audit. The new Linux build
instead pins PySide6/Qt/Shiboken 6.8.3, CTranslate2 4.8.2, SentencePiece 0.2.1
and NumPy 2.2.6. Consult PYTHON-REQUIREMENTS.txt and BUILD-INFO.json in that
package for exact versions; do not attribute Windows FFmpeg 9.0.1 to Linux.
Qt 6.8.3 sources: https://download.qt.io/official_releases/qt/6.8/6.8.3/ .
Linux wheel license files are collected alongside the existing notices during
the container build. OpenSSL 3.5.9 (Apache-2.0) is built unmodified from
https://github.com/openssl/openssl/releases/tag/openssl-3.5.9 ; its LICENSE.txt
is included. Multimedia and TLS libraries remain dynamically replaceable.

LouriÃ±a Films 0.4.0 uses unmodified dynamically loaded Qt/PySide libraries. This file does not grant a license to the LouriÃ±a Films application or to streamed films.

- PySide6, Qt Essentials, Qt Addons and Shiboken 6.12.0: the installed wheel metadata declares LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only. License texts are included here. The wheel also ships a commercial-license notice; its presence does not mean that LouriÃ±a Films holds a commercial Qt license. Upstream sources: https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://code.qt.io/cgit/qt/ . Exact release archives: https://download.qt.io/official_releases/qt/6.12/ .
- Qt Multimedia FFmpeg backend: deployed as replaceable DLLs and plugins in `_internal/PySide6`. `avcodec_license()` and `avutil_license()` report LGPL version 2.1 or later. Native runtime reports FFmpeg 9.0.1. Configuration includes shared libraries, disables static libraries, and does not enable GPL/nonfree components. Sources: https://github.com/FFmpeg/FFmpeg/tree/n9.0.1 . LGPL-2.1 text included. Zlib 1.3.1 is enabled; its license is included.
- Qt WebEngine uses Chromium and its third-party dependencies. Full upstream attribution and source information: https://doc.qt.io/qt-6/qtwebengine-licensing.html and https://code.qt.io/cgit/qt/qtwebengine-chromium.git/ . Chromium attribution is also exposed by Qt WebEngine through `chrome://credits` (not a normal LouriÃ±a Films navigation route). The player does not modify Chromium.
- Python package license files are copied from the installed distributions, with package-name prefixes. The portable package retains Python's license supplied by PyInstaller. RareFilmm's existing MIT notice is retained for previously documented architectural work; its catalog is not used.

Source rebuild instructions are in README.md. Users can replace compatible dynamic libraries in the portable `_internal` directory and rebuild the executable from source. No restriction on debugging modifications to LGPL components is introduced. Keep these notices with redistributed builds. Full third-party attribution review is required before commercial redistribution; this audit verifies the multimedia DLL license and includes the available package notices, not an independent legal certification of every Chromium component.


## Local translation added in 0.3.2

CTranslate2 4.8.2 (MIT), SentencePiece 0.2.2 (Apache-2.0), NumPy 2.5.3 and PyYAML 6.0.3 license files are included by package prefix. The runtime uses CPU inference only; CUDA/cuDNN DLLs are not distributed. Model conversion/training frameworks are not required. Public Argos models are downloaded separately on first use from the links in https://github.com/argosopentech/argospm-index ; the index is MIT/CC0. Model archives and metadata are retained under the user data directory, outside the source/portable ZIP. No model binaries are redistributed in these packages. Upstream engine sources: https://github.com/OpenNMT/CTranslate2 and https://github.com/google/sentencepiece . No Argos Translate Python code was copied; the integration uses the public model format and independently implemented sentence splitting.
