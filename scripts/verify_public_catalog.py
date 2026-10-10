"""Optional live public-catalog check using a temporary database, never user data."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from teleputin.core.config import ROOT
from teleputin.controllers.application_controller import ApplicationController
from teleputin.database.engine import create_database
from teleputin.database.repositories import Repository

QtWebEngineQuick.initialize()
QQuickStyle.setStyle("Basic")
app = QGuiApplication(sys.argv)
with tempfile.TemporaryDirectory() as directory:
    database = create_database(Path(directory) / "live.db")
    backend = ApplicationController(Repository(database))
    backend.config.update(tmdb_token="", tmdb_key="", brave_key="")
    backend.update(tmdbAvailable=False, tmdbEnabled=False)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png")))
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
    if not engine.rootObjects(): raise RuntimeError("QML failed to load")
    window = engine.rootObjects()[0]
    window.setWidth(1440)
    window.setHeight(1000)
    finished = False
    def capture():
        output = ROOT.parent / "artifacts"
        output.mkdir(exist_ok=True)
        window.grabWindow().save(str(output / "public-catalog.png"))
        print("Rows:", [(row["title"], len(row["items"])) for row in backend.state["rows"]], flush=True)
        print("Notice:", backend.state["message"], flush=True)
        print("Automatic search history:", backend.repo.recent_searches(), flush=True)
        app.quit()
    def completed():
        global finished
        if not finished and not backend.state["busy"]:
            finished = True
            QTimer.singleShot(2500, capture)
    backend.navigate("Explore")
    backend.changed.connect(completed)
    QTimer.singleShot(45000, capture)
    app.exec()
    backend.shutdown()
    del engine
    database.dispose()
