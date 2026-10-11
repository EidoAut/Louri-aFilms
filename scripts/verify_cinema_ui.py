# ==========================================================================
"""verify_cinema_ui.py
Exercise the cinema layout against public catalog snapshots and isolated data.
Remote responses are substituted; screenshots never include personal history.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Capture the four cinema states and verify overlay interactions at one size."""
    import argparse
    import json
    import sys
    import tempfile
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PySide6.QtCore import QObject, QPoint, Qt, QTimer, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QCursor, QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineQuick import QtWebEngineQuick

    from lourihna_films.controllers.application_controller import ApplicationController
    from lourihna_films.core.config import ROOT
    from lourihna_films.database.engine import create_database
    from lourihna_films.database.repositories import Repository

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--size", default="1280x720")
    args = parser.parse_args()
    width, height = map(int, args.size.split("x"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    output = ROOT.parent / "artifacts/redesign" / args.size
    output.mkdir(parents=True, exist_ok=True)
    errors = []

    def message(kind, context, text):
        if any(
            marker in text
            for marker in (
                "ReferenceError",
                "TypeError",
                "Cannot assign",
                "Unable to assign",
                "Binding loop",
                "is not a type",
                "failed to load component",
                "is unavailable",
                "Invalid property assignment",
            )
        ):
            errors.append(text)
            print(text, flush=True)

    qInstallMessageHandler(message)
    QtWebEngineQuick.initialize()
    QQuickStyle.setStyle("Basic")
    _app = QGuiApplication([])
    original_cursor = QCursor.pos()
    temp = tempfile.TemporaryDirectory()
    database = create_database(Path(temp.name) / "verification.db")
    backend = ApplicationController(Repository(database))
    backend.savePreferences("gl", False)
    movies, series = catalog["movies"], catalog["series"]

    def submit(tag, operation):
        # Substitute remote results only; retain controller transitions and QML events.
        generation = backend.generations.get(tag, 0) + 1
        backend.generations[tag] = generation
        backend.update(busy=True, loadingTask=tag)
        if tag == "details":
            item = backend.state["details"]
            result = (
                catalog["series_detail"] if item["kind"] == "tv" else catalog["detail"]
            )
        elif tag == "episodes":
            result = catalog["episodes"]
        elif tag == "candidates":
            result = {"items": []}
        elif tag == "search":
            backend.repo.remember_query(backend.state["query"])
            result = {"items": movies[:6], "more": False, "cursors": {}}
        else:
            raise AssertionError(f"Unexpected verification request: {tag}")
        QTimer.singleShot(40, lambda: backend._receive(tag, generation, result, ""))

    backend.submit = submit
    backend.update(
        rows=[
            {"title": "Popular Movies", "items": movies},
            {"title": "Popular Series", "items": series},
            {"title": "Películas · TMDB", "items": movies[8:]},
        ],
        tmdbAvailable=True,
    )
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty(
        "brandLogo", QUrl.fromLocalFile(str(ROOT / "assets/logo.png"))
    )
    engine.load(QUrl.fromLocalFile(str(ROOT / "ui/Main.qml")))
    assert engine.rootObjects(), "Main QML failed to load"
    window = engine.rootObjects()[0]
    window.setWidth(width)
    window.setHeight(height)
    window.show()
    window.requestActivate()

    def wait(milliseconds=500):
        QTest.qWait(milliseconds)

    def visual_items(item, name):
        found = [item] if item.objectName() == name else []
        for child in item.childItems():
            found.extend(visual_items(child, name))
        return found

    def item(name):
        found = window.findChild(QObject, name)
        if found is not None:
            return found
        return visual_items(window.contentItem(), name)[0]

    def point(control):
        pos = control.mapToScene(control.boundingRect().center())
        return QPoint(round(pos.x()), round(pos.y()))

    def move_pointer(position):
        # Native window-system hover events use the real cursor position too.
        if _app.platformName() != "offscreen":
            QCursor.setPos(window.mapToGlobal(position))
        QTest.mouseMove(window, position)

    def click(control):
        move_pointer(point(control))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point(control))
        wait()

    def capture(name):
        wait(350)
        assert window.grabWindow().save(str(output / f"{name}.png"))

    try:
        wait(1800)
        capture("01-portada")
        home = item("homePage")
        scroll = home.property("contentItem")
        scroll.setProperty("contentY", item("featuredBanner").height() + 45)
        wait()
        capture("02-catalogo")
        import time

        from shiboken6 import isValid

        original_cards = visual_items(window.contentItem(), "catalogCard")
        timings = []
        for busy in (True, False, True, False):
            started = time.perf_counter()
            backend.update(busy=busy)
            _app.processEvents()
            timings.append((time.perf_counter() - started) * 1000)
        retained = sum(isValid(card) for card in original_cards)
        assert retained == len(original_cards), "Loading state rebuilt catalog cards"
        print(
            f"UI updates: worst {max(timings):.1f} ms; "
            f"retained cards {retained}/{len(original_cards)}",
            flush=True,
        )
        cards = visual_items(window.contentItem(), "catalogCard")
        anchor = next(
            card
            for card in cards
            if 120 < point(card).y() < height - 100
            and 30 < point(card).x() < width - 120
        )
        move_pointer(point(anchor))
        move_pointer(QPoint(width - 30, 40))
        wait(650)
        assert not item("hoverPreview").property("visible"), (
            "Leaving a card did not cancel its pending preview"
        )
        move_pointer(point(anchor))
        wait(650)
        preview = item("hoverPreview")
        assert preview.property("visible"), "Hover did not open preview"
        assert preview.property("x") >= 0 and preview.property("y") >= 0
        assert preview.property("x") + preview.property("width") <= width
        assert preview.property("y") + preview.property("height") <= height
        capture("03-tarxeta-ampliada")
        click(item("favoriteButton"))
        assert len(backend.repo.favorites()) == 1
        click(item("favoriteButton"))
        assert backend.repo.favorites() == []
        # Keep a horizontal offset while opening/closing a modal detail sheet.
        list_view = anchor.parentItem()
        while list_view.objectName() != "carouselList":
            list_view = list_view.parentItem()
        list_view.setProperty("contentX", 40)
        vertical, horizontal = (
            scroll.property("contentY"),
            list_view.property("contentX"),
        )
        click(item("previewDetails"))
        wait()
        assert item("detailsPopup").property("visible")
        capture("04-ficha")
        QTest.keyClick(window, Qt.Key_Escape)
        wait()
        assert backend.state["page"] == "Home"
        assert item("homePage") is home, "Closing details rebuilt the catalog"
        assert abs(scroll.property("contentY") - vertical) < 1
        assert abs(list_view.property("contentX") - horizontal) < 1
        assert not item("detailsPopup").property("visible")
        # Keyboard activation must provide the same preview controls.
        anchor.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Down)
        wait()
        assert preview.property("visible")
        assert item("previewPlay").property("activeFocus")
        QTest.keyClick(window, Qt.Key_Escape)
        wait()
        assert not preview.property("visible")
        focus = window.property("activeFocusItem")
        while focus is not None and focus is not anchor:
            focus = focus.parentItem()
        assert focus is anchor, "Closing the preview did not restore card focus"
        QTest.keyClick(window, Qt.Key_Right)
        wait()
        assert (
            list_view.property("currentIndex") == anchor.property("carouselIndex") + 1
        )
        QTest.keyClick(window, Qt.Key_Left)
        wait()
        assert list_view.property("currentIndex") == anchor.property("carouselIndex")
        for edge in (
            min(cards, key=lambda c: point(c).x()),
            max((c for c in cards if point(c).x() < width), key=lambda c: point(c).x()),
        ):
            edge.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            wait()
            assert preview.property("visible")
            assert 0 <= preview.property("x") <= width - preview.property("width")
            QTest.keyClick(window, Qt.Key_Escape)
            wait()
        # Real series metadata, including supplied thumbnails and runtimes.
        backend.select(series[0])
        wait()
        from PySide6.QtCore import Q_ARG, QMetaObject

        season_index = next(
            i
            for i, season in enumerate(catalog["series_detail"]["seasons"])
            if season["season_number"] > 0
        )
        selector = item("seasonSelector")
        selector.setProperty("currentIndex", season_index)
        QMetaObject.invokeMethod(selector, "activated", Q_ARG("int", season_index))
        wait()
        details = item("detailsPage")
        details.property("contentItem").setProperty("contentY", 550)
        capture("05-episodios")
        backend.backFromDetails()
        backend.navigate("Search")
        wait()
        backend.search(movies[0]["title"])
        wait()
        assert backend.state["results"] and backend.repo.recent_searches()
        move_pointer(QPoint(10, 100))
        for _ in range(40):
            search_page = window.findChild(QObject, "searchPage")
            if search_page is not None and len(
                visual_items(search_page, "catalogCard")
            ) == len(backend.state["results"]):
                break
            wait(100)
        assert search_page is not None and search_page.property("visible")
        assert len(visual_items(search_page, "catalogCard")) == 6
        capture("06-busca")
        backend.update(
            page="Details", details={**movies[0], "poster": "", "backdrop": ""}
        )
        wait()
        capture("07-sen-imaxe")
        backend.backFromDetails()
        cached_rows = {
            "Home": [{"title": "Movies", "items": movies}],
            "Movies": [{"title": "Movies", "items": movies[2:]}],
            "Series": [{"title": "Series", "items": series}],
        }
        backend.catalog_pages.update(
            {page: (time.monotonic(), rows) for page, rows in cached_rows.items()}
        )
        navigation_times = []
        for page in ("Home", "Movies", "Series", "Home", "Movies", "Series"):
            started = time.perf_counter()
            backend.navigate(page)
            _app.processEvents()
            navigation_times.append((time.perf_counter() - started) * 1000)
            wait(200)
            assert backend.state["page"] == page
        print(
            f"Cached section dispatch: worst {max(navigation_times):.1f} ms",
            flush=True,
        )
        # Verify destructive actions only against this script's temporary database.
        watched = {
            "key": "okru:123",
            "id": "123",
            "provider": "okru",
            "kind": "video",
            "title": "History verification",
            "original_url": "https://ok.ru/video/123",
        }
        backend.repo.record_open(watched)
        backend.repo.remember_query("History verification")
        backend.repo.toggle_favorite(movies[0])
        backend.update(
            history=backend.repo.history(),
            recent=backend.repo.recent_searches(),
            favorites=backend.repo.favorites(),
        )
        QMetaObject.invokeMethod(item("manageHistoryMenu"), "triggered")
        wait()
        dialog = item("historyDialog")
        assert dialog.property("visible")
        capture("08-historiais")
        QTest.keyClick(window, Qt.Key_Escape)
        wait()
        assert not dialog.property("visible")
        assert backend.repo.history() and backend.repo.recent_searches()
        QMetaObject.invokeMethod(item("manageHistoryMenu"), "triggered")
        wait()
        item("clearWatchHistory").setProperty("checked", False)
        click(item("confirmClearHistory"))
        assert not dialog.property("visible")
        assert not backend.repo.recent_searches() and not backend.state["recent"]
        assert backend.repo.history() and backend.repo.favorites()
        QMetaObject.invokeMethod(item("manageHistoryMenu"), "triggered")
        wait()
        item("clearSearchHistory").setProperty("checked", False)
        click(item("confirmClearHistory"))
        assert not backend.repo.history() and not backend.state["history"]
        assert backend.repo.favorites()
        print(
            "PASS: history dialog cancel, selective deletion and favorites preservation"
        )
        assert not errors, "\n".join(errors)
        print(
            f"PASS {args.size}: hover, favorites, keyboard, modal, scroll retention, episodes, search and missing image"
        )
    except BaseException:
        capture("failure")
        raise
    finally:
        backend.shutdown()
        window.close()
        if _app.platformName() != "offscreen":
            QCursor.setPos(original_cursor)
        del engine
        database.dispose()
        temp.cleanup()


if __name__ == "__main__":
    main()
