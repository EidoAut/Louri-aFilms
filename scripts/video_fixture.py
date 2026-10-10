# ==========================================================================
"""video_fixture.py
Generate a tiny, silent uncompressed AVI for offline playback checks.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import struct
from pathlib import Path


def write_video_fixture(path: Path) -> None:
    """Write a deterministic uncompressed AVI for isolated playback verification."""
    width, height, frames, fps = 160, 90, 120, 4
    frame_size = width * height * 3

    def chunk(tag, data):
        return tag + struct.pack("<I", len(data)) + data + b"\0" * (len(data) % 2)

    def group(tag, data):
        return chunk(b"LIST", tag + data)

    header = struct.pack(
        "<14I",
        1000000 // fps,
        frame_size * fps,
        0,
        0,
        frames,
        0,
        1,
        frame_size,
        width,
        height,
        0,
        0,
        0,
        0,
    )
    stream = struct.pack(
        "<4s4sIHH8I4h",
        b"vids",
        b"DIB ",
        0,
        0,
        0,
        0,
        1,
        fps,
        0,
        frames,
        frame_size,
        0xFFFFFFFF,
        0,
        0,
        0,
        width,
        height,
    )
    bitmap = struct.pack(
        "<IiiHH4sIiiII", 40, width, height, 1, 24, b"\0\0\0\0", frame_size, 0, 0, 0, 0
    )
    headers = group(
        b"hdrl",
        chunk(b"avih", header)
        + group(b"strl", chunk(b"strh", stream) + chunk(b"strf", bitmap)),
    )
    video = b"".join(
        chunk(b"00db", bytes((index * 5 % 256, 0, 120)) * (width * height))
        for index in range(frames)
    )
    path.write_bytes(chunk(b"RIFF", b"AVI " + headers + group(b"movi", video)))
