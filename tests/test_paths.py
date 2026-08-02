"""Tests for :func:`scao_live.paths.safe_join`.

Covers normal joins, empty-part semantics, absolute-component override
rejection, direct traversal rejection, nested traversal rejection, and
related edge cases (literal ``..`` filenames, ``.`` segments, type
validation, and symlink-based escapes).
"""

from __future__ import annotations

import os
import sys

import pytest

from scao_live.paths import safe_join


# ---------------------------------------------------------------------------
# Normal joins
# ---------------------------------------------------------------------------


def test_normal_multipart_join(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "a", "b", "c")
    expected = os.path.realpath(os.path.join(base, "a", "b", "c"))
    assert result == expected


def test_single_part_join(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "child.txt")
    assert result == os.path.realpath(os.path.join(base, "child.txt"))


def test_returns_absolute_resolved_path(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "child")
    assert os.path.isabs(result)
    # realpath collapses any redundant separators / dot segments.
    assert result == os.path.normpath(result)


# ---------------------------------------------------------------------------
# Empty parts
# ---------------------------------------------------------------------------


def test_no_parts_returns_resolved_base(tmp_path):
    base = str(tmp_path)
    assert safe_join(base) == os.path.realpath(base)


def test_single_empty_part_returns_resolved_base(tmp_path):
    base = str(tmp_path)
    assert safe_join(base, "") == os.path.realpath(base)


def test_multiple_empty_parts_return_resolved_base(tmp_path):
    base = str(tmp_path)
    assert safe_join(base, "", "") == os.path.realpath(base)


# ---------------------------------------------------------------------------
# Absolute-part override rejection
# ---------------------------------------------------------------------------


def test_absolute_part_override_rejected(tmp_path, tmp_path_factory):
    base = str(tmp_path)
    # A sibling temp directory is absolute and outside `base`.
    outside = str(tmp_path_factory.mktemp("outside"))
    assert os.path.normcase(os.path.realpath(outside)) != os.path.normcase(
        os.path.realpath(base)
    )
    with pytest.raises(ValueError):
        safe_join(base, outside)


def test_rooted_part_override_rejected(tmp_path):
    base = str(tmp_path)
    # A rooted-but-driveless path still overrides the path portion of the
    # base on Windows and is absolute on POSIX; in both cases it escapes.
    rooted = os.sep + "escape_target"
    with pytest.raises(ValueError):
        safe_join(base, rooted)


# ---------------------------------------------------------------------------
# Direct traversal rejection
# ---------------------------------------------------------------------------


def test_direct_traversal_rejected(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "..")


def test_direct_traversal_in_middle_rejected(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "a", "..", "b")


def test_direct_traversal_at_end_rejected(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "a", "b", "..")


# ---------------------------------------------------------------------------
# Nested traversal rejection
# ---------------------------------------------------------------------------


def test_nested_traversal_rejected(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "a/../b")


def test_nested_traversal_with_separator_rejected(tmp_path):
    base = str(tmp_path)
    sep = os.sep
    with pytest.raises(ValueError):
        safe_join(base, f"a{sep}..{sep}b")


def test_nested_traversal_backslash_rejected(tmp_path):
    if sys.platform != "win32":
        pytest.skip("backslash is a path separator only on Windows")
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "a" + "\\" + ".." + "\\" + "b")


def test_traversal_inside_absolute_part_rejected(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError):
        safe_join(base, "/../etc")


# ---------------------------------------------------------------------------
# Edge cases: allowed inputs that look suspicious
# ---------------------------------------------------------------------------


def test_double_dot_filename_allowed(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "file..txt")
    assert result == os.path.realpath(os.path.join(base, "file..txt"))


def test_dot_segment_allowed(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "a", ".", "b")
    assert result == os.path.realpath(os.path.join(base, "a", "b"))


def test_trailing_separator_in_part_allowed(tmp_path):
    base = str(tmp_path)
    result = safe_join(base, "dir" + os.sep)
    assert result == os.path.realpath(os.path.join(base, "dir"))


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------


def test_non_string_base_raises_type_error():
    with pytest.raises(TypeError):
        safe_join(123, "a")  # type: ignore[arg-type]


def test_non_string_part_raises_type_error(tmp_path):
    with pytest.raises(TypeError):
        safe_join(str(tmp_path), 123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Symlink-based escape (candidate outside base without a ``..`` segment)
# ---------------------------------------------------------------------------


def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path.parent / "scao_symlink_escape_target"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "escape_link"
    try:
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(str(outside), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    try:
        with pytest.raises(ValueError):
            safe_join(str(tmp_path), "escape_link")
    finally:
        if link.is_symlink() or link.exists():
            link.unlink()
    try:
        outside.rmdir()
    except OSError:
        pass
