# ==========================================================================
"""lourihna_films.spec
Collect the desktop runtime and licensed resources for a native platform build.

Developed by EIDO Automation
"""
# ==========================================================================
# Build on Windows with: .venv\Scripts\pyinstaller lourihna_films.spec
from PyInstaller.utils.hooks import collect_dynamic_libs
a = Analysis(['main.py'], pathex=[], binaries=collect_dynamic_libs('ctranslate2'),
    datas=[('lourihna_films/ui', 'lourihna_films/ui'), ('lourihna_films/assets', 'lourihna_films/assets'), ('docs/licenses', 'licenses'), ('LICENSE', '.'), ('README.md', '.')],
    hiddenimports=['PySide6.QtMultimedia', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineCore', 'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickControls2'],
    hookspath=[], runtime_hooks=[], excludes=['tkinter'])
# Qt on Windows uses the Windows ICU API. A build-host PATH can contain
# unrelated ICU DLLs (for example Poppler's), with incompatible exports.
# Let Windows resolve its own ICU DLL instead of shipping a PATH collision.
a.binaries = [entry for entry in a.binaries if 'cudnn' not in entry[0].lower() and entry[0].lower() not in {'icuuc.dll', 'icuin.dll', 'icudt78.dll'}]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='lourihna_films',
    console=False, icon='lourihna_films/assets/lourihna_films.ico')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='lourihna_films')
