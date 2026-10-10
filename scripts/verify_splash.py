# ==========================================================================
"""verify_splash.py
Render the real welcome window and verify first-frame minimum visibility.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Capture the actual QML welcome screen using isolated startup state."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow

    from lourihna_films.core.config import ROOT
    from lourihna_films.core.startup import SPLASH_MINIMUM_MS, StartupCoordinator

    app = QGuiApplication([])
    startup = StartupCoordinator(lambda: None)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("startup", startup)
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Splash.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    assert isinstance(window, QQuickWindow)
    startup.prepared.connect(lambda result: startup.mark_ready())
    window.frameSwapped.connect(startup.shown)
    results = []

    def finish() -> None:
        results.append(startup.clock.elapsed())
        output = Path(__file__).resolve().parents[1] / "docs/screenshots/splash.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        assert window.grabWindow().save(str(output))
        app.quit()

    startup.ready.connect(finish)
    QTimer.singleShot(10000, app.quit)
    app.exec()
    startup.shutdown()
    assert results and results[0] >= SPLASH_MINIMUM_MS
    print("Real splash minimum visibility verified:", results[0], "ms")


if __name__ == "__main__":
    main()
