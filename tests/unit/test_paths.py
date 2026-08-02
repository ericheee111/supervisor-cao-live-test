"""Unit tests for :func:`scao_live.paths.safe_join`."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scao_live.paths import safe_join

# ---------------------------------------------------------------------------
# Happy path joins
# ---------------------------------------------------------------------------


def test_basic_join(tmp_path: Path) -> None:
    """Multiple components are joined under the resolved base."""
    result = safe_join(tmp_path, "a", "b", "c")
    expected = (tmp_path / "a" / "b" / "c").resolve()
    assert result == str(expected)


def test_single_part(tmp_path: Path) -> None:
    """A single component is joined correctly."""
    result = safe_join(tmp_path, "file.txt")
    expected = (tmp_path / "file.txt").resolve()
    assert result == str(expected)


def test_nested_with_separators(tmp_path: Path) -> None:
    """A component containing nested separators is handled."""
    result = safe_join(tmp_path, "a/b/c")
    expected = (tmp_path / "a" / "b" / "c").resolve()
    assert result == str(expected)


def test_empty_parts_returns_base(tmp_path: Path) -> None:
    """With no parts, the resolved base directory is returned."""
    result = safe_join(tmp_path)
    assert result == str(tmp_path.resolve())


def test_trailing_slash_part(tmp_path: Path) -> None:
    """A part with a trailing slash still joins to a valid path."""
    result = safe_join(tmp_path, "dir/")
    expected = (tmp_path / "dir").resolve()
    assert result == str(expected)


def test_returns_str(tmp_path: Path) -> None:
    """The return value is a plain ``str``, not a ``Path``."""
    result = safe_join(tmp_path, "a")
    assert isinstance(result, str)


def test_accepts_pathlike_base_and_parts(tmp_path: Path) -> None:
    """``os.PathLike`` inputs are accepted for both base and parts."""
    result = safe_join(tmp_path, Path("sub"), Path("leaf"))
    expected = (tmp_path / "sub" / "leaf").resolve()
    assert result == str(expected)


def test_dot_part_stays_in_base(tmp_path: Path) -> None:
    """A ``.`` component does not escape the base."""
    result = safe_join(tmp_path, ".", "a")
    expected = (tmp_path / "a").resolve()
    assert result == str(expected)


def test_inner_back_reference_that_stays_inside(tmp_path: Path) -> None:
    """``a/..`` resolves back to the base, which is still inside it."""
    result = safe_join(tmp_path, "a", "..")
    assert result == str(tmp_path.resolve())


# ---------------------------------------------------------------------------
# Rejection: parent traversal escaping the base
# ---------------------------------------------------------------------------


def test_reject_parent_traversal(tmp_path: Path) -> None:
    """A bare ``..`` escapes the base and is rejected."""
    with pytest.raises(ValueError, match="escapes base directory"):
        safe_join(tmp_path, "..")


def test_reject_nested_parent_traversal(tmp_path: Path) -> None:
    """Traversal deeper then up past the base is rejected."""
    with pytest.raises(ValueError, match="escapes base directory"):
        safe_join(tmp_path, "a", "..", "..")


def test_reject_deep_parent_traversal(tmp_path: Path) -> None:
    """Many ``..`` components that escape the base are rejected."""
    with pytest.raises(ValueError, match="escapes base directory"):
        safe_join(tmp_path, "..", "..", "..")


# ---------------------------------------------------------------------------
# Rejection: absolute components
# ---------------------------------------------------------------------------


def _platform_absolute_path() -> str:
    """Return a path that ``Path.is_absolute()`` considers absolute."""
    if sys.platform == "win32":
        # A drive-rooted path is absolute on Windows.
        return "C:\\Windows"
    return "/etc/passwd"


def test_reject_absolute_component(tmp_path: Path) -> None:
    """An absolute component is rejected before joining."""
    absolute = _platform_absolute_path()
    with pytest.raises(ValueError, match="Absolute path component"):
        safe_join(tmp_path, absolute)


def test_reject_absolute_component_among_parts(tmp_path: Path) -> None:
    """An absolute component appearing later in *parts* is also rejected."""
    absolute = _platform_absolute_path()
    with pytest.raises(ValueError, match="Absolute path component"):
        safe_join(tmp_path, "safe", absolute, "more")


def test_reject_rooted_component_escaping_base(tmp_path: Path) -> None:
    """A rooted-but-driveless component (e.g. ``/x``) is rejected because
    the joined result escapes the base directory."""
    # On POSIX this is caught by the absolute check; on Windows it has a
    # root but no drive and is caught by the escape check. Either way the
    # result must be a ValueError.
    with pytest.raises(ValueError):
        safe_join(tmp_path, "/escape")


# ---------------------------------------------------------------------------
# Rejection: string base that is relative
# ---------------------------------------------------------------------------


def test_relative_base_resolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative base is resolved against the CWD and still works."""
    sub = tmp_path / "workspace"
    sub.mkdir()
    monkeypatch.chdir(tmp_path)
    result = safe_join("workspace", "file.txt")
    assert result == str((sub / "file.txt").resolve())


def test_reject_absolute_component_with_str_base(tmp_path: Path) -> None:
    """Absolute rejection works with a string base too."""
    absolute = _platform_absolute_path()
    with pytest.raises(ValueError, match="Absolute path component"):
        safe_join(str(tmp_path), absolute)
