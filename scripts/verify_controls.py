"""Exercise real native controls, resume and window restoration with a local film."""
import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QUrl, QTimer, QObject, QMetaObject, Q_ARG, Qt
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtTest import QTest
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from teleputin.core.config import ROOT
from teleputin.database.engine import create_database
from teleputin.database.repositories import Repository
from teleputin.controllers.application_controller import ApplicationController
from video_fixture import write_video_fixture

QtWebEngineQuick.initialize()
QQuickStyle.setStyle("Basic")
app = QGuiApplication([])
temp = tempfile.TemporaryDirectory()
fixture = Path(temp.name) / "fixture.avi"
write_video_fixture(fixture)
second_fixture = fixture.with_name("second.avi")
shutil.copy2(fixture, second_fixture)
db = create_database(Path(temp.name) / "test.db")
repo = Repository(db)
backend = ApplicationController(repo)
entry = {"key": "okru:123", "id": "123", "provider": "okru", "kind": "video", "title": "Control verification", "original_url": "https://ok.ru/video/123", "position_ms": 4000}
repo.record_open(entry)
backend.update(page="Player", player=entry, playbackSession=8, playbackPhase="native", bufferedMedia={"url": fixture.as_uri(), "index": 0, "sources": [{"url": fixture.as_uri(), "quality": "low"}, {"url": second_fixture.as_uri(), "quality": "hd"}]})
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("backend", backend)
engine.rootContext().setContextProperty("brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png")))
engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
window = engine.rootObjects()[0]
errors = []
paused_position = 0
finished = False

def check(condition, message):
    if not condition: errors.append(message)

def native(): return window.findChild(QObject, "bufferedPlayer")
def player(): return window.findChild(QObject, "playerPage")

def pause():
    global paused_position
    check(native().property("playbackPosition") >= 4000, "Resume failed")
    window.requestActivate()
    QTest.keyClick(window, Qt.Key_Space)
    paused_position = native().property("playbackPosition")

def seek():
    check(abs(native().property("playbackPosition") - paused_position) < 300, "Pause did not hold position")
    check(native().property("playbackState") == 2, "Not paused")
    QTest.keyClick(window, Qt.Key_Right)
    backend.setVolume(0.3, False)
    QTest.keyClick(window, Qt.Key_M)
    QMetaObject.invokeMethod(native(), "changeQuality", Q_ARG("QVariant", 1))
    window.showMaximized()

def fullscreen():
    check(native().property("playbackPosition") >= paused_position + 4500, "Seek or quality resume failed")
    check(native().property("playbackState") == 2, "Quality change did not preserve pause")
    check(native().property("frameHeight") > 0, "Quality change left a blank picture")
    check(backend.state["bufferedMedia"]["index"] == 1, "Quality selection failed")
    check(abs(backend.state["volume"] - 0.3) < 0.001 and backend.state["muted"], "Volume persistence failed: " + repr((backend.state["volume"], backend.state["muted"])))
    QMetaObject.invokeMethod(player(), "toggleFullscreen")

def restore():
    check(window.visibility() == QWindow.FullScreen, "Fullscreen failed")
    QTest.keyClick(window, Qt.Key_Escape)

def close():
    global finished
    finished = True
    check(window.visibility() == QWindow.Maximized, "Maximized state not restored")
    output = ROOT.parent / "artifacts/audit-after"
    output.mkdir(parents=True, exist_ok=True)
    window.grabWindow().save(str(output / "player-controls.png"))
    QMetaObject.invokeMethod(player(), "leave")
    check(backend.state["bufferedMedia"] == {}, "Media not cleared on exit")
    check(repo.history()[0]["position_ms"] >= 8000, "Exit position not saved")
    app.quit()

for delay, callback in ((1800, pause), (2300, seek), (2800, fullscreen), (3300, restore), (3800, close)):
    QTimer.singleShot(delay, callback)
QTimer.singleShot(10000, app.quit)
app.exec()
check(finished, "Control verification timed out")
backend.shutdown()
del engine
db.dispose()
temp.cleanup()
print("CONTROL CHECK", errors or "PASS: resume, pause, seek, volume, mute, fullscreen restoration, stop and saved position")
sys.exit(bool(errors))
