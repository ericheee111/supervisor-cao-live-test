"""Tests for scao_live.paths.safe_join safety and edge-case coverage.

Covers benign joins, empty input, relative and nested bases, absolute-part
rejection (Unix and Windows), traversal rejection including embedded and
escaping ``..`` segments, and invalid input types.
"""

import pytest

from scao_live.paths import PathSafetyError, safe_join


# ---------------------------------------------------------------------------
# Benign joins
# ---------------------------------------------------------------------------


def test_basic_join():
    assert safe_join("/base", "a", "b") == "/base/a/b"


def test_single_part():
    assert safe_join("/base", "x") == "/base/x"


def test_multiple_parts():
    assert safe_join("/base", "a", "b", "c", "d") == "/base/a/b/c/d"


def test_part_with_subdirectory():
    assert safe_join("/base", "a/b") == "/base/a/b"


def test_trailing_slash_base_not_doubled():
    assert safe_join("/base/", "a") == "/base/a"


def test_backslash_separators_normalized_to_posix():
    # Backslashes in benign parts are normalized to forward slashes.
    assert safe_join("/base", "a\\b") == "/base/a/b"


# ---------------------------------------------------------------------------
# Empty input / no parts
# ---------------------------------------------------------------------------


def test_no_parts_returns_base():
    assert safe_join("/base") == "/base"


def test_no_parts_nested_base():
    assert safe_join("/base/sub") == "/base/sub"


def test_empty_string_part_skipped():
    assert safe_join("/base", "", "a") == "/base/a"


def test_all_empty_parts_returns_base():
    assert safe_join("/base", "", "") == "/base"


def test_empty_base_no_parts():
    assert safe_join("") == ""


def test_empty_base_with_part():
    # Consistent with os.path.join: empty base yields the part alone.
    assert safe_join("", "a") == "a"


# ---------------------------------------------------------------------------
# Relative and nested bases
# ---------------------------------------------------------------------------


def test_relative_base():
    assert safe_join("base", "a") == "base/a"


def test_relative_nested_base():
    assert safe_join("base/sub", "a") == "base/sub/a"


def test_nested_base():
    assert safe_join("/base/sub", "a") == "/base/sub/a"


def test_deeply_nested_base():
    assert safe_join("/a/b/c/d", "e") == "/a/b/c/d/e"


# ---------------------------------------------------------------------------
# Absolute-part rejection
# ---------------------------------------------------------------------------


def test_reject_unix_absolute_part():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "/etc/passwd")


def test_reject_absolute_part_in_middle():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "a", "/etc", "b")


def test_reject_bare_root_slash():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "/")


def test_reject_windows_drive_absolute_backslash():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "C:\\Users")


def test_reject_windows_drive_absolute_forward_slash():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "C:/Users")


def test_reject_unc_path():
    with pytest.raises(PathSafetyError):
        safe_join("/base", r"\\server\share")


def test_reject_single_backslash_part():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "\\")


# ---------------------------------------------------------------------------
# Traversal rejection (escaping ..)
# ---------------------------------------------------------------------------


def test_reject_leading_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "../x")


def test_reject_bare_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "..")


def test_reject_multiple_leading_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "../../x")


# ---------------------------------------------------------------------------
# Traversal rejection (embedded ..)
# ---------------------------------------------------------------------------


def test_reject_embedded_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "a/../b")


def test_reject_trailing_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "a/..")


def test_reject_embedded_traversal_backslash():
    with pytest.raises(PathSafetyError):
        safe_join("/base", r"a\..\b")


def test_reject_traversal_with_backslash_separator():
    with pytest.raises(PathSafetyError):
        safe_join("/base", r"..\x")


def test_reject_deeply_embedded_traversal():
    with pytest.raises(PathSafetyError):
        safe_join("/base", "a/b/../c/d")


# ---------------------------------------------------------------------------
# Invalid input types
# ---------------------------------------------------------------------------


def test_reject_non_string_base_int():
    with pytest.raises(PathSafetyError):
        safe_join(123, "a")


def test_reject_non_string_base_none():
    with pytest.raises(PathSafetyError):
        safe_join(None, "a")


def test_reject_non_string_part_int():
    with pytest.raises(PathSafetyError):
        safe_join("/base", 123)


def test_reject_non_string_part_none():
    with pytest.raises(PathSafetyError):
        safe_join("/base", None)


def test_reject_list_part():
    with pytest.raises(PathSafetyError):
        safe_join("/base", ["a"])


def test_reject_bytes_part():
    with pytest.raises(PathSafetyError):
        safe_join("/base", b"a")
