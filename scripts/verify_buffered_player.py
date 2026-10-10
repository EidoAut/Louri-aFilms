"""Opt-in public playback check; stop after three decoded frames, save no media."""
import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from PySide6.QtCore import QTimer, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink, QAudioBufferOutput
from teleputin.providers.public_media import resolve_public_media
from teleputin.providers.archive import ArchiveProvider, archive_id_from_url


async def resolve():
    async with httpx.AsyncClient() as client:
        identifier = archive_id_from_url(sys.argv[1])
        if identifier: return (await ArchiveProvider(client).playback_sources(identifier))[0]
        return await resolve_public_media(client, sys.argv[1])


if len(sys.argv) < 2:
    raise SystemExit("Provide a public video URL you are authorized to test.")
source = asyncio.run(resolve())
# Backend messages can include temporary signed URLs. Do not print them.
qInstallMessageHandler(lambda *args: None)
with open(os.devnull, "w") as quiet:
    os.dup2(quiet.fileno(), 2)
app = QGuiApplication([])
media = QMediaPlayer()
audio = QAudioOutput()
audio.setMuted(True)
media.setAudioOutput(audio)
sink = QVideoSink()
media.setVideoSink(sink)
frames = 0
audio_buffers = 0
probe = QAudioBufferOutput()
media.setAudioBufferOutput(probe)

def finish_if_ready():
    if frames >= 3 and (audio_buffers > 0 or "--require-audio" not in sys.argv):
        media.stop()
        app.quit()

def audio_ready(buffer):
    global audio_buffers
    if buffer.isValid(): audio_buffers += 1
    finish_if_ready()

probe.audioBufferReceived.connect(audio_ready)


def frame_ready(frame):
    global frames
    if frame.isValid():
        frames += 1
        finish_if_ready()


sink.videoFrameChanged.connect(frame_ready)
media.errorOccurred.connect(lambda error, message: app.quit())
media.setSource(QUrl(source["url"]))
media.play()
QTimer.singleShot(30000, app.quit)
app.exec()
media.stop()
print(f"Decoded frames: {frames}; audio buffers: {audio_buffers}; quality: {source['quality']}; media error: {media.error().name}")
sys.exit(0 if frames >= 3 and (audio_buffers > 0 or "--require-audio" not in sys.argv) else 1)
