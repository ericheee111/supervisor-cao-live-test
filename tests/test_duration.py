"""Tests for :func:`scao_live.duration.parse_duration`."""

from __future__ import annotations

import pytest

from scao_live.duration import parse_duration


@pytest.mark.parametrize(
    "value, expected",
    [
        ("500ms", 500),
        ("2s", 2_000),
        ("1m", 60_000),
        ("1h", 3_600_000),
    ],
)
def test_required_examples(value: str, expected: int) -> None:
    """The four task-specified unit examples parse correctly."""
    assert parse_duration(value) == expected


def test_zero_is_valid() -> None:
    """A zero value is nonnegative and therefore valid."""
    assert parse_duration("0ms") == 0


@pytest.mark.parametrize(
    "value",
    [
        "",
        "abc",
        "5",
        "-5s",
        "1.5s",
        "5x",
        "5ms10ms",
        " 5s",
        "5s ",
        "ms",
    ],
)
def test_malformed_or_unsupported_raises(value: str) -> None:
    """Malformed, unsupported, empty, and negative inputs raise ValueError."""
    with pytest.raises(ValueError):
        parse_duration(value)
