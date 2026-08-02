"""Tests for :func:`scao_live.paths.safe_join`.

Covers basic joins, nested parts, empty parts, direct ``..`` traversal,
embedded ``..`` traversal, absolute-part escapes, and traversal attempts
that normalise outside the base directory.
"""

from __future__ import annotations

import os

import pytest

from scao_live.paths import safe_join

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _norm(path: str) -> str:
    """Normalise *path* the same way :func:`safe_join` is expected to."""
    return os.path.normpath(path)


# ---------------------------------------------------------------------------
# Basic joins
# ---------------------------------------------------------------------------


class TestBasicJoin:
    def test_single_part(self):
        result = safe_join("base", "foo")
        assert result == _norm(os.path.join("base", "foo"))

    def test_no_parts_returns_base(self):
        result = safe_join("base")
        assert result == _norm("base")

    def test_dot_part_stays_at_base(self):
        result = safe_join("base", ".")
        assert result == _norm("base")


# ---------------------------------------------------------------------------
# Nested parts
# ---------------------------------------------------------------------------


class TestNestedParts:
    def test_three_nested_parts(self):
        result = safe_join("base", "foo", "bar", "baz")
        assert result == _norm(os.path.join("base", "foo", "bar", "baz"))

    def test_parts_with_subdirs(self):
        result = safe_join("root", "a/b", "c/d")
        assert result == _norm(os.path.join("root", "a/b", "c/d"))


# ---------------------------------------------------------------------------
# Empty parts
# ---------------------------------------------------------------------------


class TestEmptyParts:
    def test_single_empty_part(self):
        result = safe_join("base", "")
        assert result == _norm("base")

    def test_empty_part_between_real_parts(self):
        result = safe_join("base", "", "foo", "", "bar")
        assert result == _norm(os.path.join("base", "foo", "bar"))

    def test_all_parts_empty(self):
        result = safe_join("base", "", "", "")
        assert result == _norm("base")

    def test_empty_base_with_part(self):
        # An empty base normalises to "."; a child must stay within it.
        result = safe_join("", "foo")
        assert result == _norm("foo")


# ---------------------------------------------------------------------------
# Direct '..' traversal
# ---------------------------------------------------------------------------


class TestDirectTraversal:
    def test_direct_dotdot_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "..")

    def test_dotdot_after_real_part_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "foo", "..")

    def test_multiple_dotdot_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "..", "..")

    def test_dotdot_as_only_part_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base/sub", "..")


# ---------------------------------------------------------------------------
# Embedded '..' traversal (no single part equals '..')
# ---------------------------------------------------------------------------


class TestEmbeddedTraversal:
    def test_embedded_escape_rejected(self):
        # 'foo/../../..' as a single part: no part equals '..' but the
        # normalised result escapes the base.
        with pytest.raises(ValueError):
            safe_join("base", "foo/../../..")

    def test_embedded_escape_to_sibling_rejected(self):
        # 'foo/../../bar' normalises to '../bar' which is outside base.
        with pytest.raises(ValueError):
            safe_join("base", "foo/../../bar")

    def test_embedded_dotdot_within_base_accepted(self):
        # 'foo/..' normalises to 'base' — still within base, so accepted.
        result = safe_join("base", "foo/..")
        assert result == _norm("base")

    def test_embedded_dotdot_descending_accepted(self):
        # 'foo/../bar' normalises to 'base/bar' — within base.
        result = safe_join("base", "foo/../bar")
        assert result == _norm(os.path.join("base", "bar"))

    def test_deep_embedded_escape_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base/sub", "inner/../../../danger")


# ---------------------------------------------------------------------------
# Absolute-part escapes
# ---------------------------------------------------------------------------


class TestAbsolutePart:
    def test_unix_absolute_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "/etc/passwd")

    def test_leading_slash_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "/")

    @pytest.mark.skipif(os.name != "nt", reason="Windows drive-letter absolute path")
    def test_windows_drive_absolute_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "C:\\Windows")

    def test_absolute_part_after_valid_part_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "foo", "/escape")


# ---------------------------------------------------------------------------
# Traversal that normalises outside the base
# ---------------------------------------------------------------------------


class TestNormalizationOutsideBase:
    def test_sibling_path_rejected(self):
        # '../sibling' is not '..' itself but normalises outside base.
        with pytest.raises(ValueError):
            safe_join("base", "../sibling")

    def test_deep_relative_escape_rejected(self):
        with pytest.raises(ValueError):
            safe_join("base", "../../etc")

    def test_nested_base_escape_rejected(self):
        # base is 'a/b', part escapes both levels.
        with pytest.raises(ValueError):
            safe_join("a/b", "../../c")

    def test_prefix_collision_not_confused(self):
        # 'base_evil' starts with the string 'base' but is a sibling,
        # not a child.  Constructing it via traversal must be rejected.
        with pytest.raises(ValueError):
            safe_join("base", "../base_evil")

    def test_valid_deep_path_accepted(self):
        result = safe_join("base/sub", "deeper/file")
        assert result == _norm(os.path.join("base/sub", "deeper/file"))


# ---------------------------------------------------------------------------
# Error message quality
# ---------------------------------------------------------------------------


class TestErrorMessages:
    def test_absolute_error_mentions_part(self):
        with pytest.raises(ValueError, match="/etc"):
            safe_join("base", "/etc/passwd")
