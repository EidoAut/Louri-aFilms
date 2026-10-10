# ==========================================================================
"""capture_brand.py
Capture the real QML redesign using saved catalog data, without changing user data.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import json
    import os
    import sqlite3
    import sys
    import tempfile
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWebEngineQuick import QtWebEngineQuick

    from lourihna_films.controllers.application_controller import ApplicationController
    from lourihna_films.core.config import ROOT
    from lourihna_films.database.engine import create_database
    from lourihna_films.database.repositories import Repository

    path = Path(os.environ["LOCALAPPDATA"]) / "lourihna_films/lourihna_films.db"
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        items = [
            json.loads(row[0])
            for row in connection.execute(
                "SELECT payload FROM library_videos ORDER BY updated DESC LIMIT 100"
            )
        ]
        favorites = [
            json.loads(row[0])
            for row in connection.execute(
                "SELECT payload FROM favorites ORDER BY date_added DESC"
            )
        ]
    items = sorted(
        items,
        key=lambda item: bool(item.get("catalog", {}).get("poster")),
        reverse=True,
    )
    if not items:
        import asyncio

        import httpx

        from lourihna_films.providers.archive import ArchiveProvider

        async def public_catalog():
            async with httpx.AsyncClient() as client:
                return [
                    video.card()
                    for video in await ArchiveProvider(client).search(
                        "", collection="feature_films"
                    )
                ]

        items = asyncio.run(public_catalog())
    assert items, "No public or saved catalog available"
    QtWebEngineQuick.initialize()
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    temp = tempfile.TemporaryDirectory()
    db = create_database(Path(temp.name) / "capture.db")
    backend = ApplicationController(Repository(db))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty(
        "brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png"))
    )
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
    window = engine.rootObjects()[0]
    window.setWidth(1440)
    window.setHeight(900)
    if "--maximized" in sys.argv:
        window.showMaximized()
    output = ROOT.parent / "docs/screenshots/lourihna"
    output.mkdir(parents=True, exist_ok=True)
    steps = [
        (
            "home",
            {"page": "Home", "rows": [{"title": "Tu colección", "items": items[:20]}]},
        ),
        ("explore", {"page": "Explore", "exploreItems": items, "exploreMore": False}),
        ("details", {"page": "Details", "details": items[0]}),
        ("favorites", {"page": "My List", "favorites": favorites}),
        ("settings", {"page": "Settings"}),
    ]
    index = 0

    def advance():
        nonlocal index
        if index:
            suffix = "-maximized" if "--maximized" in sys.argv else ""
            window.grabWindow().save(
                str(output / (steps[index - 1][0] + suffix + ".png"))
            )
        if index == len(steps):
            app.quit()
            return
        backend.update(**steps[index][1])
        index += 1
        QTimer.singleShot(2500, advance)

    QTimer.singleShot(500, advance)
    app.exec()
    backend.shutdown()
    del engine
    db.dispose()
    temp.cleanup()
    print("Saved catalog captures:", output)


if __name__ == "__main__":
    main()
