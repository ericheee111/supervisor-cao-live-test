from __future__ import annotations

from pathlib import Path

import pytest

from scao_live.paths import safe_join


def test_single_part(tmp_path: Path) -> None:
    """A single relative part is joined underneath the resolved base."""
    result = safe_join(tmp_path, "x")
    assert Path(result) == tmp_path.resolve() / "x"


def test_multi_part(tmp_path: Path) -> None:
    """Multiple relative parts are joined in order under the base."""
    result = safe_join(tmp_path, "a", "b", "c")
    assert Path(result) == tmp_path.resolve() / "a" / "b" / "c"


def test_result_resolves_within_base(tmp_path: Path) -> None:
    """Every successful result must resolve to a path inside the base."""
    result = safe_join(tmp_path, "nested", "file.txt")
    # relative_to raises ValueError if the result is not inside the base,
    # so merely constructing it is the assertion.
    Path(result).resolve().relative_to(tmp_path.resolve())


def test_accepts_str_and_path_inputs(tmp_path: Path) -> None:
    """Both ``str`` and ``Path`` arguments are accepted for base and parts."""
    result = safe_join(str(tmp_path), Path("sub"), "leaf")
    assert Path(result) == tmp_path.resolve() / "sub" / "leaf"


def test_returns_str(tmp_path: Path) -> None:
    """The return type is a ``str``, not a ``Path``."""
    result = safe_join(tmp_path, "x")
    assert isinstance(result, str)


def test_no_parts_returns_base(tmp_path: Path) -> None:
    """With no parts, the resolved base itself is returned."""
    result = safe_join(tmp_path)
    assert Path(result) == tmp_path.resolve()


def test_internal_dotdot_that_stays_inside_is_allowed(tmp_path: Path) -> None:
    """``..`` segments that normalize back inside the base are permitted."""
    result = safe_join(tmp_path, "a", "..", "b")
    assert Path(result) == tmp_path.resolve() / "b"


def test_traversal_resolving_to_base_is_allowed(tmp_path: Path) -> None:
    """``a/..`` normalizes back to the base, which is inside the base."""
    result = safe_join(tmp_path, "a", "..")
    assert Path(result) == tmp_path.resolve()


def test_explicit_traversal_rejected(tmp_path: Path) -> None:
    """A leading ``..`` that escapes the base is rejected."""
    with pytest.raises(ValueError):
        safe_join(tmp_path, "..", "outside")


def test_nested_traversal_rejected(tmp_path: Path) -> None:
    """Traversal that escapes after descending is still rejected."""
    with pytest.raises(ValueError):
        safe_join(tmp_path, "a", "..", "..", "escape")


def test_absolute_part_rejected(tmp_path: Path) -> None:
    """An absolute path part is rejected regardless of containment."""
    absolute = tmp_path.resolve() / "inside"
    with pytest.raises(ValueError):
        safe_join(tmp_path, absolute)


def test_absolute_part_outside_base_rejected(tmp_path: Path) -> None:
    """An absolute part pointing outside the base is rejected."""
    with pytest.raises(ValueError):
        safe_join(tmp_path, "/etc", "passwd")


def test_traversal_above_base_rejected(tmp_path: Path) -> None:
    """A part chain that resolves above the base is rejected."""
    with pytest.raises(ValueError):
        safe_join(tmp_path, "..")
