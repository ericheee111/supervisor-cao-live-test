"""Tests for :func:`scao_live.paths.safe_join`.

Covers the safety requirements of the safe_join contract:

* Normal multi-part and single-part joins produce resolved paths inside base.
* Parent traversal (``..``) in any form is rejected.
* Absolute parts are rejected on every platform.
* Symlink-based escapes are rejected even when the textual path looks relative.
* Edge cases (empty parts, ``.`` components, non-existent base) behave sanely.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from scao_live.paths import safe_join


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_normal_multi_part_join(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a", "b", "c")
    assert result == (base / "a" / "b" / "c").resolve()


def test_single_part_join(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "file.txt")
    assert result == (base / "file.txt").resolve()


def test_multi_component_single_part(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a/b/c")
    assert result == (base / "a" / "b" / "c").resolve()


def test_empty_parts_returns_base(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base)
    assert result == base.resolve()


def test_dot_components_allowed(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a", ".", "b")
    assert result == (base / "a" / "b").resolve()


def test_accepts_string_base(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(str(base), "a", "b")
    assert result == (base / "a" / "b").resolve()


def test_result_is_resolved_and_inside_base(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "sub", "deep")
    # Already resolved: re-resolving must be a no-op.
    assert result.resolve() == result
    assert base.resolve() in result.parents


def test_result_is_writable(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    target = safe_join(base, "sub", "dir", "file.txt")
    target.parent.mkdir(parents=True)
    target.write_text("hello")
    assert target.read_text() == "hello"


# ---------------------------------------------------------------------------
# Parent traversal rejection
# ---------------------------------------------------------------------------


def test_parent_traversal_explicit_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..", "secret")


def test_parent_traversal_after_real_dir_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    (base / "real").mkdir(parents=True)
    with pytest.raises(ValueError):
        safe_join(base, "real", "..", "..", "secret")


def test_parent_traversal_embedded_in_part_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "a/../b")


def test_parent_traversal_only_dots_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..")


# ---------------------------------------------------------------------------
# Absolute part rejection
# ---------------------------------------------------------------------------


def test_absolute_part_posix_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "/etc", "passwd")


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows drive-letter absolute paths only meaningful on Windows",
)
def test_absolute_part_windows_drive_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "C:\\Windows", "system32")


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows root-relative absolute paths only meaningful on Windows",
)
def test_absolute_part_windows_root_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "\\Windows", "system32")


# ---------------------------------------------------------------------------
# Symlink-based escapes (defence in depth)
# ---------------------------------------------------------------------------


def _can_symlink() -> bool:
    """True if the current platform and privileges allow creating symlinks."""
    if not hasattr(os, "symlink"):
        return False
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        src.mkdir()
        dst = Path(tmp) / "dst"
        try:
            os.symlink(src, dst, target_is_directory=True)
        except (OSError, NotImplementedError):
            return False
        return dst.is_symlink()


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    if not _can_symlink():
        pytest.skip("symlinks not supported on this platform / user")

    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = base / "evil"
    os.symlink(outside, link, target_is_directory=True)

    with pytest.raises(ValueError):
        safe_join(base, "evil", "target")


def test_symlink_pointing_inside_base_allowed(tmp_path: Path) -> None:
    if not _can_symlink():
        pytest.skip("symlinks not supported on this platform / user")

    base = tmp_path / "base"
    base.mkdir()
    real_dir = base / "real"
    real_dir.mkdir()
    link = base / "link"
    os.symlink(real_dir, link, target_is_directory=True)

    result = safe_join(base, "link", "file.txt")
    # Resolved path lands inside the real (in-base) target directory.
    assert base.resolve() in result.parents
    assert result == (real_dir / "file.txt").resolve()


# ---------------------------------------------------------------------------
# Base validation
# ---------------------------------------------------------------------------


def test_base_must_exist(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        safe_join(missing, "a")


def test_value_error_messages_mention_index(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError, match="index 1"):
        safe_join(base, "ok", "..", "bad")
