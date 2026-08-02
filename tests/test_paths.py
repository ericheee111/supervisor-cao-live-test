"""Comprehensive tests for scao_live.paths.safe_join.

Covers basic joins, nested parts, empty parts, direct and embedded
``..`` traversal, absolute-part escapes, Windows absolute paths,
normalization boundaries, and error-message content.
"""

from __future__ import annotations

import pytest

from scao_live.paths import safe_join

# ---------------------------------------------------------------------------
# Basic joins (positive)
# ---------------------------------------------------------------------------


def test_basic_two_parts():
    """Two simple parts join under the base."""
    assert safe_join("/base", "a", "b") == "/base/a/b"


def test_single_part():
    """A single part appends to the base."""
    assert safe_join("/base", "x") == "/base/x"


def test_many_parts():
    """Many parts chain correctly."""
    assert safe_join("/base", "a", "b", "c", "d") == "/base/a/b/c/d"


def test_nested_part_with_separators():
    """A single part containing separators is preserved."""
    assert safe_join("/base", "a/b/c") == "/base/a/b/c"


# ---------------------------------------------------------------------------
# Empty parts (positive)
# ---------------------------------------------------------------------------


def test_empty_part_alone():
    """A lone empty part yields the normalized base."""
    assert safe_join("/base", "") == "/base"


def test_empty_part_between():
    """Empty parts between real parts are skipped."""
    assert safe_join("/base", "a", "", "b") == "/base/a/b"


def test_all_empty_parts():
    """Multiple empty parts still yield the base."""
    assert safe_join("/base", "", "", "") == "/base"


def test_no_parts():
    """No parts at all yields the normalized base."""
    assert safe_join("/base") == "/base"


# ---------------------------------------------------------------------------
# Normalization (positive)
# ---------------------------------------------------------------------------


def test_double_slash_normalized():
    """Double slashes inside a part are collapsed."""
    assert safe_join("/base", "a//b") == "/base/a/b"


def test_trailing_slash_on_base():
    """A trailing slash on the base is normalized away."""
    assert safe_join("/base/", "a") == "/base/a"


def test_trailing_slash_on_part():
    """A trailing slash on a part is normalized away."""
    assert safe_join("/base", "a/") == "/base/a"


def test_dot_component_normalized():
    """A '.' component inside a part is resolved by normalization."""
    assert safe_join("/base", "a/./b") == "/base/a/b"


def test_dot_alone():
    """A lone '.' part resolves to the base itself."""
    assert safe_join("/base", ".") == "/base"


# ---------------------------------------------------------------------------
# Direct '..' traversal rejection (negative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parts",
    [
        ("..",),
        ("..", "outside"),
        ("a", ".."),
        ("a", "..", "..", "outside"),
    ],
    ids=[
        "dotdot-alone",
        "dotdot-then-outside",
        "part-then-dotdot",
        "part-dotdot-dotdot-outside",
    ],
)
def test_direct_traversal_rejected(parts):
    """Any direct '..' component raises ValueError."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("/base", *parts)


# ---------------------------------------------------------------------------
# Embedded '..' traversal rejection (negative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parts",
    [
        ("a/../..",),
        ("a/b/../..",),
        ("../a",),
        ("a/../b",),  # Even "safe" traversal is rejected outright.
    ],
    ids=[
        "embedded-up-up",
        "embedded-deep-up",
        "embedded-leading-dotdot",
        "embedded-mid-dotdot-safe",
    ],
)
def test_embedded_traversal_rejected(parts):
    """Embedded '..' inside a multi-segment part raises ValueError."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("/base", *parts)


# ---------------------------------------------------------------------------
# Absolute-part escape rejection (negative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parts",
    [
        ("/etc/passwd",),
        ("/etc",),
        ("a", "/etc"),
        ("/",),
    ],
    ids=[
        "abs-passwd",
        "abs-etc",
        "abs-after-part",
        "abs-root",
    ],
)
def test_absolute_part_rejected(parts):
    """Any absolute Unix path part raises ValueError."""
    with pytest.raises(ValueError, match="absolute"):
        safe_join("/base", *parts)


# ---------------------------------------------------------------------------
# Windows absolute-path rejection (negative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parts",
    [
        (r"C:\Windows",),
        ("D:/secret",),
    ],
    ids=[
        "win-drive-backslash",
        "win-drive-forward-slash",
    ],
)
def test_windows_absolute_rejected(parts):
    """Windows drive-letter paths raise ValueError."""
    with pytest.raises(ValueError, match="absolute"):
        safe_join("/base", *parts)


# ---------------------------------------------------------------------------
# Normalization boundary / containment (negative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parts",
    [
        ("a/../../outside",),
        ("a/b/c/../../../..",),
    ],
    ids=[
        "normalize-escapes-1",
        "normalize-escapes-2",
    ],
)
def test_traversal_normalizing_outside_rejected(parts):
    """Traversal that would normalize outside the base is rejected."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("/base", *parts)


# ---------------------------------------------------------------------------
# Error-message content
# ---------------------------------------------------------------------------


def test_error_message_mentions_absolute():
    """The error for an absolute part mentions 'absolute'."""
    with pytest.raises(ValueError, match="absolute"):
        safe_join("/base", "/etc/passwd")


def test_error_message_mentions_traversal():
    """The error for a '..' part mentions '..'."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join("/base", "..")


def test_error_message_mentions_part_index():
    """The error includes the zero-based index of the offending part."""
    with pytest.raises(ValueError, match="part 1"):
        safe_join("/base", "a", "..")
