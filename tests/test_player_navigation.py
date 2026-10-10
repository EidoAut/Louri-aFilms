# ==========================================================================
"""test_player_navigation.py
Exercise the actual QML navigation policy in Qt's JavaScript engine.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtQml import QJSEngine


@pytest.mark.parametrize(
    "target,selected,checking,allowed",
    [
        ("https://ok.ru/videoembed/123", "https://ok.ru/videoembed/123", False, True),
        (
            "https://ok.ru/videoembed/123?autoplay=1#player",
            "https://ok.ru/videoembed/123",
            False,
            True,
        ),
        ("https://ads.example/", "https://ok.ru/videoembed/123", False, False),
        (
            "https://ok.ru.evil.example/videoembed/123",
            "https://ok.ru/videoembed/123",
            False,
            False,
        ),
        ("https://ok.ru/login", "https://ok.ru/videoembed/123", False, False),
        ("https://ok.ru/videoembed/456", "https://ok.ru/videoembed/123", False, False),
        ("javascript:alert(1)", "https://ok.ru/videoembed/123", False, False),
        ("about:blank", "https://ok.ru/videoembed/123", True, True),
        (
            "data:text/html;charset=UTF-8,probe",
            "https://ok.ru/videoembed/123",
            True,
            True,
        ),
        ("data:text/html,external", "https://ok.ru/videoembed/123", False, False),
        ("https://ads.example/", "https://ok.ru/videoembed/123", True, False),
        (
            "https://archive.org/embed/example",
            "https://archive.org/embed/example",
            False,
            True,
        ),
    ],
)
def test_player_navigation(target, selected, checking, allowed):
    _app = QCoreApplication.instance() or QCoreApplication([])
    engine = QJSEngine()
    source = (
        Path(__file__).resolve().parents[1]
        / "lourihna_films/ui/components/PlayerNavigation.js"
    )
    result = engine.evaluate(
        source.read_text(encoding="utf-8").replace(".pragma library", "")
    )
    assert not result.isError()
    function = engine.globalObject().property("allowsNavigation")
    result = function.call(
        [engine.toScriptValue(value) for value in (target, selected, checking)]
    )
    assert not result.isError()
    assert result.toBool() is allowed
