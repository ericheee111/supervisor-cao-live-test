from __future__ import annotations

from pathlib import Path

import pytest

from scao_live.paths import safe_join


def test_single_part_happy_path(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    result = safe_join(tmp_path, "subdir")
    assert result == str(tmp_path.resolve() / "subdir")
    assert Path(result).relative_to(tmp_path.resolve())


def test_multi_part_happy_path(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    result = safe_join(tmp_path, "a", "b", "file.txt")
    assert result == str(tmp_path.resolve() / "a" / "b" / "file.txt")
    assert Path(result).relative_to(tmp_path.resolve())


def test_internal_traversal_stays_in_base(tmp_path: Path) -> None:
    """A traversal that resolves back inside the base is allowed."""
    result = safe_join(tmp_path, "a", "..", "b")
    assert result == str(tmp_path.resolve() / "b")
    assert Path(result).relative_to(tmp_path.resolve())


def test_explicit_traversal_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_join(tmp_path, "..")


def test_nested_traversal_rejected(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    with pytest.raises(ValueError):
        safe_join(tmp_path, "a", "..", "..")


def test_absolute_part_rejected(tmp_path: Path) -> None:
    absolute_part = str(Path.cwd() / "evil.txt")
    assert Path(absolute_part).is_absolute()
    with pytest.raises(ValueError):
        safe_join(tmp_path, absolute_part)


def test_result_within_base_invariant(tmp_path: Path) -> None:
    resolved_base = tmp_path.resolve()
    for parts in [("a",), ("a", "b", "c"), (".", "x"), ("a", "..", "b")]:
        result = safe_join(tmp_path, *parts)
        Path(result).relative_to(resolved_base)
