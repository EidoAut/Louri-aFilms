# ==========================================================================
"""main.py
Initialize the desktop UI while a timed, responsive welcome window is visible.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from lourihna_films.database.repositories import Repository

import logging
import sys

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick

from lourihna_films.controllers.application_controller import ApplicationController
from lourihna_films.core.config import ROOT, data_directory
from lourihna_films.core.logging import configure_logging
from lourihna_films.core.startup import StartupCoordinator
from lourihna_films.database.engine import create_database
from lourihna_films.database.repositories import Repository


def prepare_database() -> Engine:
    """Migrate and recover persistent data off the GUI thread."""
    directory = data_directory()
    configure_logging(directory)
    database = create_database(directory / "lourihna_films.db")
    try:
        Repository(database).recover_library()
    except Exception:
        database.dispose()
        raise
    return database


def main() -> int:
    """Run the Qt event loop; return a failure status when startup is unavailable."""
    if "--smoke-translation" in sys.argv:
        import json

        from lourihna_films.services.translation_service import TranslationService

        index = sys.argv.index("--smoke-translation")
        model, output = Path(sys.argv[index + 1]), Path(sys.argv[index + 2])
        try:
            result = TranslationService(model.parent, None).infer(
                model, "A young woman returns home and discovers a secret."
            )
            output.write_text(json.dumps({"translation": result}), encoding="utf-8")
            return 0 if result else 1
        except Exception as exc:
            output.write_text(
                json.dumps({"error": type(exc).__name__}), encoding="utf-8"
            )
            return 1
    QQuickStyle.setStyle("Basic")
    QtWebEngineQuick.initialize()
    app = QGuiApplication(sys.argv)
    app.setApplicationName("lourihna_films")
    app.setApplicationDisplayName("Louriña Films")
    app.setOrganizationName("LourihnaFilms")
    app.setApplicationVersion("0.4.0")
    app.setWindowIcon(QIcon(str(ROOT / "assets" / "lourihna_films.ico")))
    startup = StartupCoordinator(prepare_database)
    splash_engine = QQmlApplicationEngine()
    splash_engine.rootContext().setContextProperty("startup", startup)
    splash_engine.load(QUrl.fromLocalFile(str(ROOT / "ui" / "Splash.qml")))
    if not splash_engine.rootObjects():
        startup.shutdown()
        return 1
    splash = splash_engine.rootObjects()[0]
    splash.frameSwapped.connect(startup.shown)
    resources = {}

    def prepared(database):
        resources["database"] = database
        try:
            controller = ApplicationController(Repository(database), recover=False)
            resources["controller"] = controller
            engine = QQmlApplicationEngine()
            resources["engine"] = engine
            engine.rootContext().setContextProperty("backend", controller)
            engine.rootContext().setContextProperty("startup", startup)
            engine.rootContext().setContextProperty(
                "brandLogo", QUrl.fromLocalFile(str(ROOT / "assets" / "logo.png"))
            )
            engine.load(QUrl.fromLocalFile(str(ROOT / "ui" / "Main.qml")))
            if not engine.rootObjects():
                startup.fail()
                return
            window = engine.rootObjects()[0]
            resources["window"] = window

            def check_ready():
                if window.property("contentReady"):
                    startup.mark_ready()

            window.contentReadyChanged.connect(check_ready)
            check_ready()
        except Exception:
            logging.exception("Main window initialization failed")
            startup.fail()

    def reveal():
        """Show the prepared main window after both startup gates have passed."""
        if "--smoke-test" in sys.argv:
            print(f"SPLASH_READY_MS={startup.clock.elapsed()}", flush=True)
        window = resources["window"]
        controller = resources["controller"]
        window.show()
        window.requestActivate()
        splash.close()
        QTimer.singleShot(0, lambda: controller.navigate("Home"))
        if "--smoke-test" in sys.argv:
            QTimer.singleShot(
                1200,
                lambda: controller.update(
                    page="Player",
                    playbackPhase="web",
                    player={
                        "title": "Startup verification",
                        "embed_url": "about:blank",
                    },
                ),
            )
            if "--smoke-media" in sys.argv:
                fixture = (
                    Path(sys.argv[sys.argv.index("--smoke-media") + 1])
                    .resolve()
                    .as_uri()
                )
                QTimer.singleShot(
                    2400,
                    lambda: controller.update(
                        playbackPhase="native", bufferedMedia={"url": fixture}
                    ),
                )

                def finish_smoke():
                    native = window.findChild(QObject, "bufferedPlayer")
                    passed = (
                        native
                        and not native.property("failure")
                        and native.property("playbackPosition") > 0
                    )
                    controller.update(bufferedMedia={})
                    app.exit(0 if passed else 1)

                QTimer.singleShot(6500, finish_smoke)
            else:
                QTimer.singleShot(2400, lambda: controller.navigate("Search"))
                QTimer.singleShot(3000, app.quit)

    startup.prepared.connect(prepared)
    startup.ready.connect(reveal)
    app.aboutToQuit.connect(startup.shutdown)
    result = app.exec()
    if resources.get("controller"):
        resources["controller"].shutdown()
    resources.pop("engine", None)
    if resources.get("database"):
        resources["database"].dispose()
    return 1 if startup.error_message else result


if __name__ == "__main__":
    sys.exit(main())
