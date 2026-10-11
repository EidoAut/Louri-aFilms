# ==========================================================================
"""verify_controls.py
Exercise real native controls, resume and window restoration with a local film.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import shutil
    import sys
    import tempfile
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QTimer, QUrl
    from PySide6.QtGui import QGuiApplication, QWindow
    from PySide6.QtMultimedia import QAudioOutput, QMediaDevices
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    from video_fixture import write_video_fixture

    from lourihna_films.controllers.application_controller import ApplicationController
    from lourihna_films.core.config import ROOT
    from lourihna_films.database.engine import create_database
    from lourihna_films.database.repositories import Repository

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
    entry = {
        "key": "okru:123",
        "id": "123",
        "provider": "okru",
        "kind": "video",
        "title": "Control verification",
        "original_url": "https://ok.ru/video/123",
        "position_ms": 4000,
    }
    repo.record_open(entry)
    backend.update(
        page="Player",
        player=entry,
        playbackSession=8,
        playbackPhase="native",
        bufferedMedia={
            "url": fixture.as_uri(),
            "index": 0,
            "sources": [
                {"url": fixture.as_uri(), "quality": "low"},
                {"url": second_fixture.as_uri(), "quality": "hd"},
            ],
        },
    )
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty(
        "brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png"))
    )
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
    window = engine.rootObjects()[0]
    errors = []
    paused_position = 0
    finished = False

    def check(condition, message):
        if not condition:
            errors.append(message)

    def native():
        return window.findChild(QObject, "bufferedPlayer")

    def player():
        return window.findChild(QObject, "playerPage")

    def pause():
        nonlocal paused_position
        check(native().property("playbackPosition") >= 4000, "Resume failed")
        window.requestActivate()
        QTest.keyClick(window, Qt.Key_Space)
        paused_position = native().property("playbackPosition")

    def seek():
        check(
            abs(native().property("playbackPosition") - paused_position) < 300,
            "Pause did not hold position",
        )
        check(native().property("playbackState") == 2, "Not paused")
        output = window.findChild(QAudioOutput, "playbackAudioOutput")
        check(output is not None, "Audio output missing")
        if output is not None:
            check(
                output.device().id() == QMediaDevices.defaultAudioOutput().id(),
                "Audio did not follow the default output",
            )
            outputs = QMediaDevices.audioOutputs()
            print(f"AUDIO ROUTING: {len(outputs)} available outputs checked")
            for device in outputs:
                native().setProperty("selectedAudioId", bytes(device.id()).decode())
                app.processEvents()
                check(
                    output.device().id() == device.id(), "Manual output routing failed"
                )
                check(
                    native().property("playbackState") == 2,
                    "Audio routing resumed video",
                )
            native().setProperty("selectedAudioId", "")
            app.processEvents()
            check(
                output.device().id() == QMediaDevices.defaultAudioOutput().id(),
                "Automatic audio routing was not restored",
            )
            check(
                abs(output.volume() - backend.state["volume"]) < 0.001,
                "Audio routing changed volume",
            )
            menu_button = window.findChild(QObject, "audioOutputButton")
            QMetaObject.invokeMethod(menu_button, "clicked")
            app.processEvents()
            menu = window.findChild(QObject, "audioOutputMenu")
            check(
                menu is not None and menu.property("visible"), "Audio menu did not open"
            )
            if menu is not None:
                QMetaObject.invokeMethod(menu, "close")
        QTest.keyClick(window, Qt.Key_Right)
        backend.setVolume(0.3, False)
        QTest.keyClick(window, Qt.Key_M)
        QMetaObject.invokeMethod(native(), "changeQuality", Q_ARG("QVariant", 1))
        window.showMaximized()

    def fullscreen():
        check(
            native().property("playbackPosition") >= paused_position + 4500,
            "Seek or quality resume failed",
        )
        check(
            native().property("playbackState") == 2,
            "Quality change did not preserve pause",
        )
        check(
            native().property("frameHeight") > 0, "Quality change left a blank picture"
        )
        check(backend.state["bufferedMedia"]["index"] == 1, "Quality selection failed")
        check(
            abs(backend.state["volume"] - 0.3) < 0.001 and backend.state["muted"],
            "Volume persistence failed: "
            + repr((backend.state["volume"], backend.state["muted"])),
        )
        QMetaObject.invokeMethod(player(), "toggleFullscreen")

    def restore():
        check(window.visibility() == QWindow.FullScreen, "Fullscreen failed")
        QTest.keyClick(window, Qt.Key_Escape)

    def close():
        nonlocal finished
        finished = True
        check(window.visibility() == QWindow.Maximized, "Maximized state not restored")
        output = ROOT.parent / "artifacts/audit-after"
        output.mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(output / "player-controls.png"))
        QMetaObject.invokeMethod(player(), "leave")
        check(backend.state["bufferedMedia"] == {}, "Media not cleared on exit")
        check(repo.history()[0]["position_ms"] >= 8000, "Exit position not saved")
        app.quit()

    for delay, callback in (
        (1800, pause),
        (2300, seek),
        (2800, fullscreen),
        (3300, restore),
        (3800, close),
    ):
        QTimer.singleShot(delay, callback)
    QTimer.singleShot(10000, app.quit)
    app.exec()
    check(finished, "Control verification timed out")
    backend.shutdown()
    del engine
    db.dispose()
    temp.cleanup()
    print(
        "CONTROL CHECK",
        errors
        or "PASS: resume, pause, seek, volume, mute, fullscreen restoration, stop and saved position",
    )
    sys.exit(bool(errors))


if __name__ == "__main__":
    main()
