"""Desktop entry point; initialize WebEngine before creating the GUI."""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QUrl, QTimer, QObject
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from teleputin.core.config import ROOT, data_directory
from teleputin.core.logging import configure_logging
from teleputin.database.engine import create_database
from teleputin.database.repositories import Repository
from teleputin.controllers.application_controller import ApplicationController


def main():
    if "--smoke-translation" in sys.argv:
        import json
        from teleputin.services.translation_service import TranslationService
        index = sys.argv.index("--smoke-translation")
        model = Path(sys.argv[index + 1])
        output = Path(sys.argv[index + 2])
        try:
            result = TranslationService(model.parent, None).infer(model, "A young woman returns home and discovers a secret.")
            output.write_text(json.dumps({"translation": result}), encoding="utf-8")
            return 0 if result else 1
        except Exception as exc:
            output.write_text(json.dumps({"error": type(exc).__name__}), encoding="utf-8")
            return 1
    directory = data_directory()
    configure_logging(directory)
    QQuickStyle.setStyle("Basic")
    QtWebEngineQuick.initialize()
    app = QGuiApplication(sys.argv)
    app.setApplicationName("TelePutin")
    app.setApplicationDisplayName("Louriña Films")
    app.setOrganizationName("TelePutin")
    app.setApplicationVersion("0.3.4")
    app.setWindowIcon(QIcon(str(ROOT / "assets" / "teleputin.ico")))
    database = create_database(directory / "teleputin.db")
    controller = ApplicationController(Repository(database))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty("brandLogo", QUrl.fromLocalFile(str(ROOT / "assets" / "logo.png")))
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui" / "Main.qml")))
    if not engine.rootObjects():
        controller.shutdown()
        return 1
    window = engine.rootObjects()[0]
    app.aboutToQuit.connect(controller.shutdown)
    QTimer.singleShot(700, lambda: controller.navigate("Home"))
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(1200, lambda: controller.update(page="Player", playbackPhase="web", player={"title": "Startup verification", "embed_url": "about:blank"}))
        if "--smoke-media" in sys.argv:
            fixture = Path(sys.argv[sys.argv.index("--smoke-media") + 1]).resolve().as_uri()
            QTimer.singleShot(2400, lambda: controller.update(playbackPhase="native", bufferedMedia={"url": fixture}))
            def finish_smoke():
                native = window.findChild(QObject, "bufferedPlayer")
                passed = native and not native.property("failure") and native.property("playbackPosition") > 0
                controller.update(bufferedMedia={})
                app.exit(0 if passed else 1)
            QTimer.singleShot(6500, finish_smoke)
        else:
            QTimer.singleShot(2400, lambda: controller.navigate("Search"))
            QTimer.singleShot(3000, app.quit)
    result = app.exec()
    del engine
    database.dispose()
    return result


if __name__ == "__main__":
    sys.exit(main())
