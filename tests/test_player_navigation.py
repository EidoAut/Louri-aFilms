# ==========================================================================
"""test_player_navigation.py
Exercise the actual QML navigation policy in Qt's JavaScript engine.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import json
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


@pytest.mark.parametrize(
    "samples,restarts",
    [
        ([120, 10, 11, 12], 3),
        ([120, 0, 1, 2], 3),
        ([120, 120, 120], 1),
        ([10, 11, 12], 3),
    ],
)
def test_web_monitor_recognizes_progress_after_rewinding(samples, restarts):
    _app = QCoreApplication.instance() or QCoreApplication([])
    engine = QJSEngine()
    source = (
        Path(__file__).resolve().parents[1] / "lourihna_films/ui/pages/PlayerPage.qml"
    ).read_text(encoding="utf-8")
    callback = source.split("function(raw) {", 1)[1].split("\n        })", 1)[0]
    result = engine.evaluate(
        """
        var restarts = 0, lastTime = -1, session = 1;
        var player = {webActive: true, webStarted: false, failure: ""};
        var backend = {viewState: {playbackSession: 1}};
        var webStart = {stop: function() {}};
        var webStall = {restart: function() {restarts++}, stop: function() {}};
        var Strings = {t: function(a, b) {return a}};
        var tick = function(raw) {
        """
        + callback
        + "};"
        + "var samples = "
        + json.dumps(samples)
        + "; samples.forEach(function(time) {"
        + "tick(JSON.stringify([{time: time, paused: false, error: false}]));});"
        + "restarts;"
    )
    assert not result.isError(), result.toString()
    assert result.toInt() == restarts
