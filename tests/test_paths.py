"""Tests for :func:`scao_live.paths.safe_join`.

Covers the safety requirements of the safe_join contract:

* Normal multi-part and single-part joins produce resolved paths inside base.
* Parent traversal (``..``) in any form is rejected.
* Absolute parts are rejected on every platform.
* Symlink-based escapes are rejected even when the textual path looks relative.
* Edge cases (empty parts, ``.`` components, non-existent base) behave sanely.

These tests are the regression suite for the safety contract. They MUST stay
in place; removing them re-opens the traversal/symlink escape vulnerabilities.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from scao_live.paths import safe_join


# ---------------------------------------------------------------------------
# Helpers
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


# ---------------------------------------------------------------------------
# Happy path (8 tests)
# ---------------------------------------------------------------------------


def test_normal_multi_part_join(tmp_path: Path) -> None:
    """Multi-part join returns a resolved path equal to base/a/b/c."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a", "b", "c")
    assert result == (base / "a" / "b" / "c").resolve()


def test_single_part_join(tmp_path: Path) -> None:
    """A single part is joined under base and resolved."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "file.txt")
    assert result == (base / "file.txt").resolve()


def test_multi_component_single_part(tmp_path: Path) -> None:
    """A part that itself contains separators is joined component-wise."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a/b/c")
    assert result == (base / "a" / "b" / "c").resolve()


def test_empty_parts_returns_base(tmp_path: Path) -> None:
    """With no parts, the resolved base itself is returned."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base)
    assert result == base.resolve()


def test_dot_components_allowed(tmp_path: Path) -> None:
    """``.`` components are not traversal and must be accepted."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a", ".", "b")
    assert result == (base / "a" / "b").resolve()


def test_accepts_string_base(tmp_path: Path) -> None:
    """A ``str`` base is accepted alongside ``Path`` bases."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(str(base), "a", "b")
    assert result == (base / "a" / "b").resolve()


def test_result_is_resolved_and_inside_base(tmp_path: Path) -> None:
    """The returned path is fully resolved and lives inside base."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "sub", "deep")
    assert result.resolve() == result
    assert base.resolve() in result.parents


def test_result_is_writable(tmp_path: Path) -> None:
    """The returned path can actually be used to write a file under base."""
    base = tmp_path / "base"
    base.mkdir()
    target = safe_join(base, "sub", "dir", "file.txt")
    target.parent.mkdir(parents=True)
    target.write_text("hello")
    assert target.read_text() == "hello"


# ---------------------------------------------------------------------------
# Parent traversal rejection (6 tests)
# ---------------------------------------------------------------------------


def test_parent_traversal_explicit_rejected(tmp_path: Path) -> None:
    """An explicit ``..`` part must be rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..", "secret")


def test_parent_traversal_after_real_dir_rejected(tmp_path: Path) -> None:
    """Traversal after a real directory still escapes and is rejected."""
    base = tmp_path / "base"
    (base / "real").mkdir(parents=True)
    with pytest.raises(ValueError):
        safe_join(base, "real", "..", "..", "secret")


def test_parent_traversal_embedded_in_part_rejected(tmp_path: Path) -> None:
    """A ``..`` embedded inside a single part string is rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "a/../b")


def test_parent_traversal_only_dots_rejected(tmp_path: Path) -> None:
    """A bare ``..`` part with nothing else is rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..")


def test_nested_traversal_deep_rejected(tmp_path: Path) -> None:
    """Multiple chained ``..`` parts are all rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..", "..", "..", "etc")


def test_traversal_with_separator_in_part_rejected(tmp_path: Path) -> None:
    """A ``../x`` embedded in a single part string is rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "../x")


# ---------------------------------------------------------------------------
# Absolute part rejection (4 tests)
# ---------------------------------------------------------------------------


def test_absolute_part_posix_rejected(tmp_path: Path) -> None:
    """A POSIX absolute path part must be rejected on every platform."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "/etc", "passwd")


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows drive-letter absolute paths only meaningful on Windows",
)
def test_absolute_part_windows_drive_rejected(tmp_path: Path) -> None:
    """A Windows drive-letter absolute part is rejected on Windows."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, r"C:\Windows", "system32")


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows root-relative absolute paths only meaningful on Windows",
)
def test_absolute_part_windows_root_rejected(tmp_path: Path) -> None:
    """A Windows root-relative (backslash) absolute part is rejected."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, r"\Windows", "system32")


def test_absolute_part_resets_join_rejected(tmp_path: Path) -> None:
    """An absolute part must not reset the join to the filesystem root."""
    base = tmp_path / "base"
    base.mkdir()
    # On POSIX, /etc/passwd would reset os.path.join to /etc/passwd.
    # On Windows, /etc is root-relative and also resets. Either way it must
    # be rejected, never returning a path outside base.
    with pytest.raises(ValueError):
        safe_join(base, "/absolute", "path")


# ---------------------------------------------------------------------------
# Symlink-based escapes (3 tests, defence in depth)
# ---------------------------------------------------------------------------


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    """A symlink inside base pointing outside base must be rejected."""
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
    """A symlink whose target lives inside base is accepted (resolved)."""
    if not _can_symlink():
        pytest.skip("symlinks not supported on this platform / user")

    base = tmp_path / "base"
    base.mkdir()
    real_dir = base / "real"
    real_dir.mkdir()
    link = base / "link"
    os.symlink(real_dir, link, target_is_directory=True)

    result = safe_join(base, "link", "file.txt")
    assert base.resolve() in result.parents
    assert result == (real_dir / "file.txt").resolve()


def test_symlink_chain_escape_rejected(tmp_path: Path) -> None:
    """A chain of symlinks ultimately escaping base is rejected."""
    if not _can_symlink():
        pytest.skip("symlinks not supported on this platform / user")

    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    # base/link1 -> base/link2 -> outside
    link2 = base / "link2"
    os.symlink(outside, link2, target_is_directory=True)
    link1 = base / "link1"
    os.symlink(link2, link1, target_is_directory=True)

    with pytest.raises(ValueError):
        safe_join(base, "link1", "target")


# ---------------------------------------------------------------------------
# Base validation & types (4 tests)
# ---------------------------------------------------------------------------


def test_base_must_exist(tmp_path: Path) -> None:
    """A non-existent base must raise FileNotFoundError (cannot resolve)."""
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        safe_join(missing, "a")


def test_value_error_messages_mention_index(tmp_path: Path) -> None:
    """ValueError messages identify the offending part index for debugging."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError, match="index 1"):
        safe_join(base, "ok", "..", "bad")


def test_safe_join_returns_path_object(tmp_path: Path) -> None:
    """The return value is always a :class:`pathlib.Path` instance."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, "a")
    assert isinstance(result, Path)


def test_pathlib_path_input_accepted(tmp_path: Path) -> None:
    """``Path`` objects are accepted for both base and parts."""
    base = tmp_path / "base"
    base.mkdir()
    result = safe_join(base, Path("a"), Path("b"))
    assert result == (base / "a" / "b").resolve()
