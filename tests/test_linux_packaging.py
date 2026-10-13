# ==========================================================================
"""test_linux_packaging.py
Protect the compatibility gate against understated or private GLIBC imports.

Developed by EIDO Automation
"""

# ==========================================================================
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from scripts.verify_linux_elf import required_glibc


def test_only_imported_glibc_versions_are_counted():
    """Exported versions do not constitute dependencies of an ELF consumer."""
    output = (
        "Version definition section Name: GLIBC_2.40\n"
        "Version needs section Name: GLIBC_2.9 Name: GLIBC_2.31"
    )
    assert required_glibc(output) == (2, 31)


def test_high_glibc_import_is_detected():
    """A single new requirement must dominate older imported symbols."""
    assert required_glibc("Version needs section Name: GLIBC_2.38") > (2, 31)


@pytest.mark.parametrize("symbol", ["GLIBC_PRIVATE", "GLIBC_ABI_DT_RELR"])
def test_private_and_abi_requirements_are_rejected(symbol):
    """Never silently treat nonnumeric GLIBC imports as compatible."""
    with pytest.raises(ValueError):
        required_glibc("Version needs section Name: " + symbol)


def test_qt_tls_backend_is_available():
    """A loadable GUI without HTTPS would break artwork and network playback."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtNetwork import QSslSocket

    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None
    assert QSslSocket.supportsSsl()


@pytest.fixture
def installer_fixture(tmp_path):
    """Build an isolated installer fixture backed by a real loadable ELF."""
    if sys.platform != "linux":
        pytest.skip("Linux installer contract")
    root = Path(__file__).resolve().parents[1]
    home = tmp_path / "home with spaces"
    home.mkdir()
    source = tmp_path / "package"
    internal = source / "_internal"
    icon = internal / "lourihna_films/assets/logo.png"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(b"fixture")
    (source / "BUILD-INFO.json").write_text("{}")
    executable = source / "lourihna_films"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    library = Path(sysconfig.get_config_var("LIBDIR")) / sysconfig.get_config_var(
        "LDLIBRARY"
    )
    for relative in (
        "libpython3.12.so.1.0",
        "PySide6/Qt/lib/libQt6Core.so.6",
        "PySide6/Qt/lib/libQt6Gui.so.6",
        "PySide6/Qt/lib/libQt6Multimedia.so.6",
        "PySide6/Qt/lib/libQt6WebEngineCore.so.6",
        "PySide6/Qt/plugins/platforms/libqxcb.so",
    ):
        destination = internal / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(library, destination)
    for action in ("install", "uninstall"):
        shutil.copy2(root / f"packaging/{action}-linux.sh", source / f"{action}.sh")
    return source, home, {**os.environ, "HOME": str(home)}


def test_installer_update_uninstall_preserves_profile(installer_fixture):
    """Updates replace obsolete runtime files and uninstalls preserve user data."""
    source, home, environment = installer_fixture
    command = ["bash", str(source / "install.sh")]
    subprocess.run(command, env=environment, check=True, capture_output=True)
    target = home / ".local/opt/lourinha-films"
    (target / "obsolete").write_text("old")
    profile = home / ".local/share/lourihna_films"
    profile.mkdir()
    (profile / "user.db").write_text("keep")
    subprocess.run(command, env=environment, check=True, capture_output=True)
    assert not (target / "obsolete").exists()
    subprocess.run(["bash", str(target / "uninstall.sh")], env=environment, check=True)
    assert not target.exists()
    assert (profile / "user.db").read_text() == "keep"


def test_installer_refuses_unowned_and_symlink_destinations(installer_fixture):
    """Neither installation nor uninstallation can replace unrelated files."""
    source, home, environment = installer_fixture
    target = home / ".local/opt/lourinha-films"
    target.mkdir(parents=True)
    sentinel = target / "unrelated"
    sentinel.write_text("keep")
    for action in ("install", "uninstall"):
        result = subprocess.run(["bash", str(source / f"{action}.sh")], env=environment)
        assert result.returncode != 0
        assert sentinel.read_text() == "keep"
    sentinel.unlink()
    target.rmdir()
    target.symlink_to(source, target_is_directory=True)
    for action in ("install", "uninstall"):
        result = subprocess.run(["bash", str(source / f"{action}.sh")], env=environment)
        assert result.returncode != 0
        assert (source / "lourihna_films").is_file()
