"""Tests for :func:`scao_live.duration.parse_duration`."""

import pytest

from scao_live.duration import parse_duration

# ---------------------------------------------------------------------------
# Required conversions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("input_str", "expected_ms"),
    [
        ("100ms", 100),
        ("5s", 5_000),
        ("2m", 120_000),
        ("1h", 3_600_000),
    ],
)
def test_required_conversions(input_str: str, expected_ms: int) -> None:
    """The four required unit-to-millisecond conversions."""
    assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Case-insensitive units
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("input_str", "expected_ms"),
    [
        ("100MS", 100),
        ("100Ms", 100),
        ("100mS", 100),
        ("5S", 5_000),
        ("2M", 120_000),
        ("1H", 3_600_000),
    ],
)
def test_case_insensitive_units(input_str: str, expected_ms: int) -> None:
    """Unit suffixes are matched case-insensitively."""
    assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Surrounding whitespace
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("input_str", "expected_ms"),
    [
        ("  5s", 5_000),
        ("5s  ", 5_000),
        ("  5s  ", 5_000),
        ("\t5s\t", 5_000),
        ("\n5s\n", 5_000),
    ],
)
def test_surrounding_whitespace_stripped(input_str: str, expected_ms: int) -> None:
    """Leading and trailing whitespace is ignored."""
    assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Zero and large integer values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("input_str", "expected_ms"),
    [
        ("0ms", 0),
        ("0s", 0),
        ("0m", 0),
        ("0h", 0),
        ("999999999ms", 999_999_999),
        ("1000000s", 1_000_000_000),
        ("50000m", 3_000_000_000),
        ("1000h", 3_600_000_000),
    ],
)
def test_zero_and_large_values(input_str: str, expected_ms: int) -> None:
    """Zero and large nonnegative integers are accepted."""
    assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_str",
    [
        # Empty
        "",
        "   ",
        "\t\n",
        # Malformed — no unit
        "5",
        "123",
        # Malformed — no value
        "s",
        "ms",
        "m",
        "h",
        # Malformed — non-numeric
        "abc",
        "five_seconds",
        # Combined units
        "1h30m",
        "1m30s",
        "1h30m20s",
        "2m15s",
        # Negative
        "-5s",
        "-1ms",
        "-100m",
        # Decimal
        "1.5s",
        "0.5m",
        "3.14h",
        "2.0s",
        # Unknown unit
        "5x",
        "5sec",
        "5minutes",
        "5d",
        "5y",
        # Internal whitespace (only surrounding whitespace is stripped)
        "5 s",
        "5  s",
        "100 ms",
        "1h 30m",
    ],
)
def test_invalid_inputs_raise_value_error(input_str: str) -> None:
    """All invalid inputs must raise ValueError."""
    with pytest.raises(ValueError):
        parse_duration(input_str)
