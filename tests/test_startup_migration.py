# ==========================================================================
"""test_startup_migration.py
Verify startup readiness gates and lossless legacy database migration.

Developed by EIDO Automation
"""

# ==========================================================================
import sqlite3
import threading
import time

from PySide6.QtCore import QCoreApplication

from lourihna_films.core.compatibility import (
    DATABASE_NAME,
    LEGACY_DATABASE,
    migrate_data,
)
from lourihna_films.core.startup import StartupCoordinator


def pump(app, predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    assert predicate()


def test_fast_start_waits_from_shown_frame():
    app = QCoreApplication.instance() or QCoreApplication([])
    startup = StartupCoordinator(lambda: None, minimum_ms=80)
    startup.prepared.connect(lambda result: startup.mark_ready())
    ready = []
    startup.ready.connect(lambda: ready.append(time.monotonic()))
    app.processEvents()
    assert not startup.clock.isValid()
    started = time.monotonic()
    startup.shown()
    pump(app, lambda: bool(ready))
    assert ready[0] - started >= 0.08
    startup.shutdown()


def test_slow_start_does_not_add_another_minimum_interval():
    app = QCoreApplication.instance() or QCoreApplication([])
    release = threading.Event()
    startup = StartupCoordinator(lambda: release.wait(2), minimum_ms=80)
    startup.prepared.connect(lambda result: startup.mark_ready())
    startup.shown()
    pump(app, lambda: startup.clock.elapsed() >= 120)
    assert not startup.finished
    before = time.monotonic()
    release.set()
    pump(app, lambda: startup.finished)
    assert time.monotonic() - before < 0.08
    startup.shutdown()


def test_failed_start_is_closable_and_never_ready():
    app = QCoreApplication.instance() or QCoreApplication([])

    def fail():
        raise RuntimeError("fixture failure")

    startup = StartupCoordinator(fail, minimum_ms=1)
    startup.shown()
    pump(app, lambda: bool(startup.error_message))
    assert not startup.finished and not startup.timer.isActive()
    startup.shutdown()


def test_close_during_load_does_not_publish_result():
    app = QCoreApplication.instance() or QCoreApplication([])
    release = threading.Event()
    startup = StartupCoordinator(lambda: (release.wait(2), None)[1], minimum_ms=1)
    prepared = []
    startup.prepared.connect(prepared.append)
    startup.shown()
    startup.shutdown()
    release.set()
    app.processEvents()
    startup.poll()
    assert prepared == [] and not startup.finished


def test_migration_preserves_original_and_existing_destination(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    with sqlite3.connect(old / LEGACY_DATABASE) as database:
        database.execute("create table favorites (title text)")
        database.execute("insert into favorites values ('Saved film')")
    original = (old / LEGACY_DATABASE).read_bytes()
    migrate_data(new, old)
    assert (old / LEGACY_DATABASE).read_bytes() == original
    with sqlite3.connect(new / DATABASE_NAME) as database:
        assert (
            database.execute("select title from favorites").fetchone()[0]
            == "Saved film"
        )
        database.execute("update favorites set title='New choice'")
    migrate_data(new, old)
    with sqlite3.connect(new / DATABASE_NAME) as database:
        assert (
            database.execute("select title from favorites").fetchone()[0]
            == "New choice"
        )
