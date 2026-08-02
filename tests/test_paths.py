"""Tests for :func:`scao_live.paths.safe_join`."""

from __future__ import annotations

import pytest

from scao_live.paths import safe_join


# ---------------------------------------------------------------------------
# Benign joins
# ---------------------------------------------------------------------------


def test_single_part():
    assert safe_join("foo", "bar") == "foo/bar"


def test_multiple_parts():
    assert safe_join("foo", "bar", "baz", "qux") == "foo/bar/baz/qux"


def test_returns_str_type():
    result = safe_join("foo", "bar")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# No parts
# ---------------------------------------------------------------------------


def test_no_parts_returns_base_unchanged():
    assert safe_join("foo") == "foo"


def test_no_parts_returns_absolute_base_unchanged():
    assert safe_join("/abs/path") == "/abs/path"


def test_no_parts_returns_empty_base_unchanged():
    assert safe_join("") == ""


# ---------------------------------------------------------------------------
# Relative and nested bases
# ---------------------------------------------------------------------------


def test_relative_base():
    assert safe_join("rel/base", "sub") == "rel/base/sub"


def test_nested_base_preserved():
    assert safe_join("a/b/c", "d") == "a/b/c/d"


def test_absolute_base_preserved():
    assert safe_join("/home/user", "data") == "/home/user/data"


def test_base_not_normalized_double_slash():
    # The trusted base is never normalized; double slashes are preserved.
    assert safe_join("foo//bar", "baz") == "foo//bar/baz"


def test_base_with_traversal_preserved():
    # The trusted base is not validated for '..'; it is returned verbatim.
    assert safe_join("foo/../bar", "baz") == "foo/../bar/baz"


# ---------------------------------------------------------------------------
# Absolute-part rejection
# ---------------------------------------------------------------------------


def test_leading_slash_rejected():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "/etc/passwd")


def test_leading_backslash_rejected():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "\\Windows\\system32")


def test_drive_letter_rejected():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "C:Windows")


def test_drive_letter_with_slash_rejected():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "D:/secret")


def test_absolute_in_second_part_rejected():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "ok", "/escape")


def test_lone_slash_rejected_as_absolute():
    with pytest.raises(ValueError, match="absolute"):
        safe_join("foo", "/")


# ---------------------------------------------------------------------------
# Traversal rejection (including embedded '..')
# ---------------------------------------------------------------------------


def test_dotdot_only_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "..")


def test_leading_dotdot_slash_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "../bar")


def test_trailing_slash_dotdot_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "bar/..")


def test_embedded_dotdot_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "a/../b")


def test_backslash_traversal_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "a\\..\\b")


def test_dotdot_in_second_part_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "ok", "../escape")


def test_multiple_dotdots_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "../../etc")


def test_dotdot_with_backslash_leading_rejected():
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("foo", "..\\secret")


# ---------------------------------------------------------------------------
# Invalid input types
# ---------------------------------------------------------------------------


def test_non_string_base_int():
    with pytest.raises(TypeError, match="base"):
        safe_join(123, "bar")


def test_non_string_base_none():
    with pytest.raises(TypeError, match="base"):
        safe_join(None, "bar")


def test_non_string_part_int():
    with pytest.raises(TypeError, match="parts"):
        safe_join("foo", 123)


def test_non_string_part_none():
    with pytest.raises(TypeError, match="parts"):
        safe_join("foo", None)


def test_non_string_part_list():
    with pytest.raises(TypeError, match="parts"):
        safe_join("foo", ["bar"])


def test_non_string_part_in_second_position():
    with pytest.raises(TypeError, match=r"parts\[1\]"):
        safe_join("foo", "ok", 3.14)


def test_non_string_part_bytes():
    with pytest.raises(TypeError, match="parts"):
        safe_join("foo", b"bar")


# ---------------------------------------------------------------------------
# Edge cases that should succeed
# ---------------------------------------------------------------------------


def test_single_dot_part_allowed():
    # '.' is a valid directory reference, not traversal.
    assert safe_join("foo", ".", "bar") == "foo/./bar"


def test_filename_containing_dotdot_allowed():
    # 'foo..bar' is a regular filename, not a '..' segment.
    assert safe_join("dir", "foo..bar") == "dir/foo..bar"


def test_ellipsis_allowed():
    # '...' is not '..' and is a valid filename on most systems.
    assert safe_join("dir", "...") == "dir/..."


def test_unicode_part_allowed():
    assert safe_join("dir", "file\u00e9") == "dir/file\u00e9"
