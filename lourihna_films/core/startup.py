# ==========================================================================
"""startup.py
Coordinate first-frame splash timing and cancellable background preparation.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable

from PySide6.QtCore import Property, QElapsedTimer, QObject, QTimer, Signal

SPLASH_MINIMUM_MS = 3000
STARTUP_POLL_MS = 50


class StartupCoordinator(QObject):
    """Own initialization; release the main window only after timing and readiness."""

    changed = Signal()
    prepared = Signal(object)
    ready = Signal()

    def __init__(self, prepare: Callable, minimum_ms: int = SPLASH_MINIMUM_MS) -> None:
        super().__init__()
        self.minimum_ms = minimum_ms
        self.prepare = prepare
        self.clock = QElapsedTimer()
        self.error_message = ""
        self.window_ready = False
        self.finished = False
        self.closed = False
        self.future = None
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="lourihna-startup"
        )
        self.timer = QTimer(self)
        self.timer.setInterval(STARTUP_POLL_MS)
        self.timer.timeout.connect(self.poll)

    @Property(str, notify=changed)
    def errorMessage(self) -> str:
        """Expose only an actionable, credential-free startup error to QML."""
        return self.error_message

    def shown(self) -> None:
        """Start the monotonic interval on the first rendered splash frame."""
        if self.closed or self.clock.isValid():
            return
        self.clock.start()
        self.future = self.executor.submit(self.prepare)
        self.timer.start()

    def mark_ready(self) -> None:
        """Record successful main QML loading on the GUI thread."""
        self.window_ready = True
        self.poll()

    def fail(self) -> None:
        """Keep a closable error screen if initialization cannot complete."""
        self.error_message = "No se pudo iniciar la aplicación. Cierra e inténtalo de nuevo. / Non se puido iniciar a aplicación. Pecha e téntao de novo."
        self.timer.stop()
        self.changed.emit()

    def poll(self) -> None:
        """Deliver worker results on the GUI thread and enforce both readiness gates."""
        if self.closed or self.finished or self.error_message:
            return
        if self.future is not None and self.future.done():
            future, self.future = self.future, None
            try:
                self.prepared.emit(future.result())
            except Exception:
                logging.error("Application initialization failed", exc_info=True)
                self.fail()
                return
        if (
            self.window_ready
            and self.clock.isValid()
            and self.clock.elapsed() >= self.minimum_ms
        ):
            self.finished = True
            self.timer.stop()
            self.ready.emit()

    def shutdown(self) -> None:
        """Stop UI callbacks; close any prepared repository without showing a window."""
        self.closed = True
        self.timer.stop()
        if self.future is not None:

            def dispose_result(future):
                if future.cancelled():
                    return
                try:
                    result = future.result()
                    if result is not None:
                        result.dispose()
                except Exception:
                    logging.warning("Startup worker ended after closing")

            self.future.add_done_callback(dispose_result)
        self.executor.shutdown(wait=False, cancel_futures=True)
