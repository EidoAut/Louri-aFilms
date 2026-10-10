# ==========================================================================
"""verify_ui.py
Launch real QML pages against a temporary database and capture visual evidence.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import asyncio
    import os
    import sys
    import tempfile
    from pathlib import Path

    import httpx

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PySide6.QtCore import (
        QMetaObject,
        QObject,
        QTimer,
        QUrl,
        qInstallMessageHandler,
    )
    from PySide6.QtGui import QColor, QGuiApplication, QImage
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWebEngineQuick import QtWebEngineQuick

    from lourihna_films.controllers.application_controller import ApplicationController
    from lourihna_films.core.config import ROOT
    from lourihna_films.database.engine import create_database
    from lourihna_films.database.repositories import Repository

    explore_count = 2000 if "--stress-explore" in sys.argv else 40
    errors = []

    def message(kind, context, message):
        print(message, flush=True)
        if "invalid-artwork" in message:
            return
        if any(
            x in message
            for x in (
                "Error:",
                "Unexpected token",
                "is not a type",
                "Cannot assign",
                "failed to load component",
                "Unable to assign",
                "not assigned a valid texture",
                "Cannot open:",
                "Binding loop detected",
            )
        ):
            errors.append(message)

    qInstallMessageHandler(message)
    QtWebEngineQuick.initialize()
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    temp = tempfile.TemporaryDirectory()
    database = create_database(Path(temp.name) / "ui.db")
    controller = ApplicationController(Repository(database))
    if "--galician" in sys.argv:
        controller.savePreferences("gl", False)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty(
        "brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png"))
    )
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    window = engine.rootObjects()[0]
    window.setWidth(
        960 if "--compact" in sys.argv else 1440 if "--wide" in sys.argv else 1280
    )
    window.setHeight(
        640 if "--compact" in sys.argv else 1000 if "--wide" in sys.argv else 720
    )
    output = (
        ROOT.parent
        / "artifacts"
        / (
            "compact"
            if "--compact" in sys.argv
            else "wide"
            if "--wide" in sys.argv
            else "standard"
        )
    )
    if "--galician" in sys.argv:
        output = output.with_name(output.name + "-gl")
    if os.environ.get("QT_SCALE_FACTOR"):
        output = output.with_name(output.name + "-dpi")
    output.mkdir(exist_ok=True, parents=True)
    sample = {
        "id": 42,
        "kind": "tv",
        "key": "tv:42",
        "title": "UI verification · Series",
        "year": "2026",
        "overview": "A local fixture verifies layout and controls without claiming any real streaming availability.",
        "poster": "",
        "backdrop": "",
        "rating": 8.2,
        "genres": ["Drama"],
        "runtime": 50,
        "alternatives": ["Alternative title"],
        "seasons": [{"name": "Season 1", "season_number": 1}],
        "related": [],
    }
    artwork = list((ROOT.parent / "artifacts" / "qa-artwork").glob("*.img"))
    if artwork:
        sample.update(
            poster=artwork[0].resolve().as_uri(), backdrop=artwork[0].resolve().as_uri()
        )
    from video_fixture import write_video_fixture

    video_fixture = Path(temp.name) / "fixture.avi"
    write_video_fixture(video_fixture)
    native_url = video_fixture.as_uri()
    if "--native-public" in sys.argv:
        from lourihna_films.providers.public_media import resolve_public_media

        async def resolve_native():
            async with httpx.AsyncClient() as client:
                return await resolve_public_media(
                    client, sys.argv[sys.argv.index("--native-public") + 1]
                )

        native_url = asyncio.run(resolve_native())["url"]
        with open(os.devnull, "w") as quiet:
            os.dup2(quiet.fileno(), 2)
    steps = [
        ("home", {"page": "Home"}),
        (
            "catalog",
            {
                "page": "Home",
                "rows": [
                    {
                        "title": "Layout verification",
                        "items": [
                            {**sample, "id": i, "key": f"tv:{i}"} for i in range(8)
                        ],
                    }
                ],
            },
        ),
        (
            "search",
            {
                "page": "Search",
                "query": "Example",
                "results": [
                    {
                        **sample,
                        "title": "Monty.Python.and.the.Holy.Grail.1975.720p.Dual.DVD.Extended.Edition.Long.Title.Without.Spaces",
                    },
                    sample,
                ],
                "recent": ["Example"],
            },
        ),
        (
            "details",
            {
                "page": "Details",
                "details": sample,
                "episodes": [
                    {
                        "name": "First episode",
                        "episode_number": 1,
                        "season_number": 1,
                        "overview": "An episode description.",
                        "still": "",
                    }
                ],
            },
        ),
        (
            "candidates",
            {
                "page": "Details",
                "details": sample,
                "candidates": [
                    {
                        "kind": "video",
                        "provider": "okru",
                        "id": "123",
                        "key": "okru:123",
                        "title": "UI verification candidate",
                        "source_name": "OK.ru public search",
                        "duration_seconds": 5400,
                        "match_reason": "Title match · Similar runtime",
                        "poster": "",
                        "original_url": "https://ok.ru/video/123",
                    }
                ],
                "episodes": [],
            },
        ),
        (
            "video-details",
            {
                "page": "Details",
                "details": {
                    "id": "123",
                    "key": "okru:123",
                    "kind": "video",
                    "title": "Public link layout verification",
                    "category": "Documentaries",
                    "duration_seconds": 125,
                    "metadata_status": "Public page metadata",
                    "original_url": "https://ok.ru/video/123",
                },
                "episodes": [],
            },
        ),
        ("import", {"page": "Search"}),
        (
            "explore",
            {
                "page": "Explore",
                "exploreItems": [
                    {**sample, "key": f"tv:{i}"} for i in range(explore_count)
                ],
                "exploreMore": False,
            },
        ),
        ("favorites", {"page": "My List", "favorites": [sample]}),
        ("settings", {"page": "Settings"}),
        (
            "player-loading",
            {
                "page": "Player",
                "playbackPhase": "loading",
                "bufferedMedia": {},
                "player": {
                    "provider": "archive",
                    "title": "Loading verification",
                    "embed_url": "about:blank",
                },
            },
        ),
        (
            "player-error",
            {
                "page": "Player",
                "playbackPhase": "error",
                "player": {
                    "provider": "archive",
                    "title": "Unavailable source verification",
                    "embed_url": "about:blank",
                },
            },
        ),
        (
            "buffered-player",
            {
                "page": "Player",
                "playbackPhase": "native",
                "bufferedMedia": {"url": native_url},
                "player": {
                    "title": "Native player verification",
                    "embed_url": "about:blank",
                },
            },
        ),
        (
            "player",
            {
                "page": "Player",
                "playbackPhase": "idle",
                "bufferedMedia": {},
                "player": {
                    "title": "Player lifecycle verification",
                    "embed_url": "about:blank",
                },
            },
        ),
        ("return", {"page": "Search", "player": {}}),
    ]
    for label, size in (
        ("small-thumbnail", (200, 120)),
        ("portrait-artwork", (1000, 1500)),
        ("wide-artwork", (3840, 2160)),
        ("tmdb-backdrop", (1280, 720)),
    ):
        fixture = QImage(*size, QImage.Format_RGB32)
        fixture.fill(QColor("#780000"))
        path = Path(temp.name) / f"{label}.png"
        fixture.save(str(path))
        entry = {
            **sample,
            "poster": path.as_uri(),
            "backdrop": "",
            "title": f"Artwork verification: {label}",
        }
        steps.insert(
            2,
            (
                label,
                {
                    "page": "Home",
                    "rows": [{"title": "Artwork verification", "items": [entry]}],
                },
            ),
        )
    invalid_artwork = Path(temp.name) / "invalid-artwork.png"
    invalid_artwork.write_bytes(b"invalid image for fallback verification")
    steps.insert(
        2,
        (
            "failed-backdrop",
            {
                "page": "Home",
                "rows": [
                    {
                        "title": "Fallback verification",
                        "items": [
                            {
                                **sample,
                                "poster": (
                                    Path(temp.name) / "portrait-artwork.png"
                                ).as_uri(),
                                "backdrop": invalid_artwork.as_uri(),
                            }
                        ],
                    }
                ],
            },
        ),
    )
    index = 0

    def step():
        nonlocal index
        if index:
            previous = steps[index - 1][0]
            if previous == "search":

                def find_visual(item, name):
                    if item.objectName() == name:
                        return item
                    for child in item.childItems():
                        found = find_visual(child, name)
                        if found is not None:
                            return found
                    return None

                button = find_visual(window.contentItem(), "favoriteButton")
                if not button:
                    errors.append("Favorite action missing")
                else:
                    for expected_saved in (True, False):
                        QMetaObject.invokeMethod(button, "clicked")
                        app.processEvents()
                        persisted = controller.repo.favorites()
                        expected_label = (
                            "Quitar"
                            if expected_saved
                            else ("Engadir" if "--galician" in sys.argv else "Añadir")
                        )
                        if (
                            bool(persisted) != expected_saved
                            or button.property("text") != expected_label
                        ):
                            errors.append(
                                "Favorite action or persisted state did not update"
                            )
                    print("FAVORITES add/remove persisted", flush=True)
            if previous == "explore":
                grid = window.findChild(QObject, "exploreGrid")
                calls = []
                original_submit = controller.submit

                def capture_page(tag, operation):
                    calls.append(tag)
                    controller.generations[tag] = 100
                    controller.update(busy=True)

                controller.submit = capture_page
                controller.explore_active = ["Movies"]
                controller.update(exploreMore=True, exploreNumber=1)
                grid.setProperty(
                    "contentY", grid.property("contentHeight") - grid.height()
                )
                app.processEvents()
                position = grid.property("contentY")
                # An exhausted/duplicate page must not recursively fetch another page.
                controller._receive(
                    "exploreMore",
                    100,
                    {"rows": [], "active": ["Movies"], "number": 2},
                    "",
                )
                for _ in range(5):
                    app.processEvents()
                if calls != ["exploreMore"]:
                    errors.append("Discovery chained requests without another scroll")
                if calls != ["exploreMore"]:
                    errors.append(
                        "Scrolling did not request exactly one discovery page"
                    )
                controller._receive(
                    "exploreMore",
                    100,
                    {
                        "rows": [
                            {
                                "items": [
                                    {**sample, "key": f"tv:{i}"}
                                    for i in range(explore_count, explore_count + 20)
                                ]
                            }
                        ],
                        "active": [],
                        "number": 2,
                    },
                    "",
                )
                app.processEvents()
                for _ in range(5):
                    app.processEvents()
                print(
                    "EXPLORE position/count",
                    position,
                    grid.property("contentY"),
                    grid.property("count"),
                    flush=True,
                )
                if (
                    abs(grid.property("contentY") - position) > 1
                    or grid.property("count") != explore_count + 20
                ):
                    errors.append(
                        "Appending discovery results changed the scroll position or count"
                    )
                controller.submit = original_submit
                print(
                    "EXPLORE automatic paging and scroll retention", calls, flush=True
                )
            if previous == "buffered-player":
                native = window.findChild(QObject, "bufferedPlayer")
                print(
                    "NATIVE",
                    native.property("failure") if native else "missing",
                    native.property("playbackPosition") if native else None,
                    native.property("playbackStatus") if native else None,
                    native.property("playbackState") if native else None,
                    flush=True,
                )
                if (
                    not native
                    or native.property("failure")
                    or native.property("playbackPosition") <= 0
                ):
                    errors.append("Native playback did not advance")
            if previous in (
                "small-thumbnail",
                "portrait-artwork",
                "wide-artwork",
                "failed-backdrop",
                "tmdb-backdrop",
            ):
                hero = window.findChild(QObject, "heroArtwork")
                expected = True
                if not hero or hero.property("wideArtwork") != expected:
                    errors.append(f"Incorrect background selection for {previous}")
                print(
                    "ARTWORK",
                    previous,
                    hero.property("wideArtwork") if hero else None,
                    flush=True,
                )
            window.grabWindow().save(str(output / f"{steps[index - 1][0]}.png"))
        if index == len(steps):
            app.quit()
            return
        name, state = steps[index]
        print("VERIFY", name, flush=True)
        controller.update(**state)
        if name == "candidates":
            QTimer.singleShot(
                100,
                lambda: (
                    window.findChild(QObject, "detailsPage")
                    .property("contentItem")
                    .setProperty("contentY", 500)
                ),
            )
        if name == "import":
            QTimer.singleShot(
                100,
                lambda: QMetaObject.invokeMethod(
                    window.findChild(QObject, "importDialog"), "open"
                ),
            )
        index += 1
        QTimer.singleShot(
            (15000 if "--native-public" in sys.argv else 3500)
            if name == "buffered-player"
            else 800,
            step,
        )

    QTimer.singleShot(900, step)
    app.exec()
    controller.shutdown()
    del engine
    database.dispose()
    temp.cleanup()
    print(f"QML errors: {len(errors)}", errors, flush=True)
    sys.exit(bool(errors))


if __name__ == "__main__":
    main()
