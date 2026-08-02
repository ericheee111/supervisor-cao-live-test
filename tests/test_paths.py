"""Tests for :func:`scao_live.paths.safe_join`.

Covers normal joins, empty parts, absolute-part override rejection,
direct and nested traversal rejection, type rejection, and symlink
escape rejection.
"""

import os

import pytest

from scao_live.paths import safe_join


# ── Normal operation ────────────────────────────────────────────────

def test_basic_join():
    """Multi-part join matches os.path.join for safe components."""
    assert safe_join('/base', 'a', 'b') == '/base/a/b'


def test_single_part():
    """Single safe part is appended correctly."""
    assert safe_join('/base', 'x') == '/base/x'


def test_multi_part_join():
    """Many safe parts are joined correctly."""
    assert safe_join('/base', 'a', 'b', 'c', 'd') == '/base/a/b/c/d'


def test_valid_nested_path():
    """Deeply nested valid path works."""
    assert safe_join('/base', 'a', 'b', 'c') == '/base/a/b/c'


# ── Empty parts ─────────────────────────────────────────────────────

def test_empty_parts():
    """No parts returns the resolved base."""
    assert safe_join('/base') == '/base'


def test_empty_string_part():
    """A single empty string part collapses to the resolved base."""
    assert safe_join('/base', '') == '/base'


def test_base_with_trailing_sep():
    """Trailing separator on base is normalised away."""
    assert safe_join('/base/', 'a', 'b') == '/base/a/b'


# ── Dot (current directory) — allowed ──────────────────────────────

def test_dot_part_allowed():
    """Single '.' (current dir) is not '..' and is allowed."""
    result = safe_join('/base', '.', 'a')
    assert result == '/base/a'


# ── Absolute-part override rejection ───────────────────────────────

def test_absolute_part_rejected():
    """An absolute path in parts overrides base and must be rejected."""
    with pytest.raises(ValueError, match="escapes base"):
        safe_join('/base', '/etc/passwd')


def test_absolute_part_rejected_partial():
    """Absolute path in a later part still overrides and is rejected."""
    with pytest.raises(ValueError, match="escapes base"):
        safe_join('/base', 'a', '/etc/passwd')


# ── Traversal ('..') rejection ─────────────────────────────────────

def test_direct_traversal_rejected():
    """Direct '..' is rejected by the component check."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join('/base', '..')


def test_nested_traversal_rejected():
    """'..' in a later part is rejected by the component check."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join('/base', 'a', '..', '..')


def test_traversal_in_component_rejected():
    """'..' embedded inside a single component is rejected."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join('/base', 'a/../../../etc')


def test_traversal_dotdot_suffix_rejected():
    """'a/..' pattern is rejected."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join('/base', 'a/..')


def test_backslash_traversal_rejected():
    """'..' reached via backslash separator is also rejected."""
    with pytest.raises(ValueError, match=r"\.\."):
        safe_join('/base', 'a\\..\\..')


# ── Type rejection ─────────────────────────────────────────────────

def test_non_string_part_rejected():
    """Non-string parts are rejected with a clear error."""
    with pytest.raises(ValueError, match="must be a string"):
        safe_join('/base', 123)


def test_non_string_part_rejected_none():
    """None as a part is rejected."""
    with pytest.raises(ValueError, match="must be a string"):
        safe_join('/base', None)


def test_non_string_part_rejected_list():
    """A list as a part is rejected."""
    with pytest.raises(ValueError, match="must be a string"):
        safe_join('/base', ['a'])


# ── Symlink escape rejection ───────────────────────────────────────

def test_symlink_escape_rejected(tmp_path):
    """A symlink inside base that points outside must be rejected."""
    base = tmp_path / 'base'
    base.mkdir()

    outside = tmp_path / 'outside'
    outside.mkdir()

    evil = base / 'evil'
    evil.symlink_to(outside)

    with pytest.raises(ValueError, match="escapes base"):
        safe_join(str(base), 'evil', 'passwd')


def test_symlink_to_base_subdir_allowed(tmp_path):
    """A symlink to a real subdirectory within base is allowed."""
    base = tmp_path / 'base'
    base.mkdir()

    real_dir = base / 'real_dir'
    real_dir.mkdir()

    link = base / 'link'
    link.symlink_to(real_dir)

    result = safe_join(str(base), 'link', 'file.txt')
    # realpath resolves the symlink, so the result should be inside
    # the real directory.
    assert result == str(real_dir / 'file.txt')
    assert result.startswith(str(base))
