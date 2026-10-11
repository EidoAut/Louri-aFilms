# ==========================================================================
"""secrets.py
Windows DPAPI protection tied to the current Windows user.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import base64
import ctypes
import os
import uuid
from ctypes import wintypes

SESSION_SECRETS = {}
WINDOWS = os.name == "nt"


class Blob(ctypes.Structure):
    """Describe a Windows DPAPI byte buffer for ctypes interoperability."""

    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_byte))]


def transform(value: bytes, decrypt: bool = False) -> bytes:
    """Protect or decrypt bytes with Windows DPAPI; raise RuntimeError on failure."""
    if os.name != "nt":
        raise RuntimeError(
            "Saved credentials require Windows DPAPI. Use environment variables on other systems."
        )
    buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    output = Blob()
    if decrypt:
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source), None, None, None, None, 0, ctypes.byref(output)
        )
    else:
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(source),
            "LourihnaFilms",
            None,
            None,
            None,
            0,
            ctypes.byref(output),
        )
    if not ok:
        raise RuntimeError("Windows could not protect or read the saved credential.")
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        ctypes.windll.kernel32.LocalFree(output.data)


def protect(value: str) -> str:
    """Protect a secret with DPAPI or return a session-only reference on other systems."""
    if not value:
        return ""
    if WINDOWS:
        return "dpapi:" + base64.b64encode(transform(value.encode())).decode()
    # A functional session-only fallback never writes a plaintext credential.
    reference = "session:" + uuid.uuid4().hex
    SESSION_SECRETS[reference] = value
    return reference


def reveal(value: str) -> str:
    """Resolve a protected or session-only credential without logging its value."""
    if not value:
        return ""
    if value.startswith("session:"):
        return SESSION_SECRETS.get(value, "")
    if not value.startswith("dpapi:"):
        return ""
    if not WINDOWS:
        return ""
    try:
        return transform(base64.b64decode(value[6:], validate=True), True).decode()
    except ValueError as exc:
        raise RuntimeError("The saved credential is invalid. Enter it again.") from exc
