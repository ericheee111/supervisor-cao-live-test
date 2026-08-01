"""Tests for :func:`scao_live.paths.safe_join`."""

import os

import pytest

from scao_live.paths import safe_join


def test_safe_join_single_part():
    """safe_join joins a base with a single part."""
    assert safe_join('/base', 'file.txt') == os.path.join('/base', 'file.txt')


def test_safe_join_multiple_parts():
    """safe_join joins a base with multiple parts."""
    result = safe_join('/base', 'subdir', 'file.txt')
    assert result == os.path.join('/base', 'subdir', 'file.txt')


def test_safe_join_no_extra_parts():
    """safe_join returns the base when no extra parts are supplied."""
    assert safe_join('/base') == '/base'


def test_safe_join_traversal_raises():
    """safe_join raises for traversal input containing '..'."""
    with pytest.raises(ValueError):
        safe_join('/base', '../etc/passwd')


def test_safe_join_traversal_in_base_raises():
    """safe_join raises when the base itself contains '..'."""
    with pytest.raises(ValueError):
        safe_join('/base/..', 'subdir')


def test_safe_join_traversal_in_middle_part_raises():
    """safe_join raises when a middle part contains '..'."""
    with pytest.raises(ValueError):
        safe_join('/base', 'a', '../b', 'c')
