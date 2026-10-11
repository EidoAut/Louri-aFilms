# ==========================================================================
"""test_release_export.py
Check that source exports retain new code while refusing tracked personal data.

Developed by EIDO Automation
"""

# ==========================================================================
import subprocess
import zipfile

import pytest

from scripts import package_release


def test_source_export_excludes_local_profile(tmp_path, monkeypatch):
    """Export untracked source but never ignored credentials or databases."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setattr(package_release, "ROOT", tmp_path)
    (tmp_path / ".gitignore").write_text(".env\n*.db\noutput/\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.5.0"\n', encoding="utf-8"
    )
    (tmp_path / "new.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=test-only\n", encoding="utf-8")
    (tmp_path / "profile.db").write_bytes(b"test-only")
    output = tmp_path / "output"
    output.mkdir()
    archive_path = package_release.export_source(output)
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {".gitignore", "pyproject.toml", "new.py"}


@pytest.mark.parametrize("name", [".env", "profile.db", "profile.db-wal"])
def test_source_export_rejects_tracked_private_files(tmp_path, monkeypatch, name):
    """Git tracking cannot override the release privacy boundary."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setattr(package_release, "ROOT", tmp_path)
    (tmp_path / name).write_text("test-only", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", name], check=True)
    with pytest.raises(ValueError, match="Private/generated file"):
        package_release.source_files()
