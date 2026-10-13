# ==========================================================================
"""verify_linux_audio.py
Decode a local generated tone through Qt and exercise virtual audio routing.
This is a headless check, not evidence of sound from physical speakers.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import math
import struct
import tempfile
import wave
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import (
    QAudioBufferOutput,
    QAudioOutput,
    QMediaDevices,
    QMediaPlayer,
)


def main() -> None:
    """Require decoded audio buffers and a real PulseAudio virtual sink."""
    app = QGuiApplication([])
    assert QMediaDevices.audioOutputs(), "No virtual audio device available"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "tone.wav"
        with wave.open(str(path), "wb") as output:
            output.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
            output.writeframes(
                b"".join(
                    struct.pack(
                        "<h", int(8000 * math.sin(2 * math.pi * 440 * n / 44100))
                    )
                    for n in range(44100 * 3)
                )
            )
        player = QMediaPlayer()
        audio = QAudioOutput()
        audio.setVolume(0.3)
        player.setAudioOutput(audio)
        probe = QAudioBufferOutput()
        player.setAudioBufferOutput(probe)
        buffers = []
        errors = []
        probe.audioBufferReceived.connect(
            lambda buffer: buffers.append(buffer.byteCount())
            if buffer.isValid()
            else None
        )
        player.errorOccurred.connect(lambda error, message: errors.append(message))
        player.setSource(QUrl.fromLocalFile(str(path)))
        player.play()
        QTimer.singleShot(2500, app.quit)
        app.exec()
        assert not errors, errors
        assert sum(buffers) > 0 and player.position() > 0, "Audio did not decode"
        assert abs(audio.volume() - 0.3) < 0.001
        audio.setMuted(True)
        assert audio.isMuted()
        player.stop()
    print("PASS: decoded PCM audio, virtual device, volume and mute")


if __name__ == "__main__":
    main()
