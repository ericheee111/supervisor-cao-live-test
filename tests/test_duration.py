"""Tests for :func:`scao_live.duration.parse_duration`.

Covers every supported unit, expected conversion examples, case
insensitivity, surrounding whitespace, zero and large values, decimal
inputs, and every rejection path (non-string, empty, malformed, compound,
and unsupported-unit inputs).
"""

from __future__ import annotations

import pytest

from scao_live.duration import parse_duration

# ---------------------------------------------------------------------------
# Happy path: supported units and expected conversion examples
# ---------------------------------------------------------------------------


class TestSupportedUnits:
    """Each unit suffix converts using its millisecond factor."""

    @pytest.mark.parametrize(
        ("value", "unit", "expected_ms"),
        [
            (100, "ms", 100),
            (2, "s", 2_000),
            (1, "m", 60_000),
            (1, "h", 3_600_000),
        ],
    )
    def test_unit_conversion(self, value: int, unit: str, expected_ms: int) -> None:
        assert parse_duration(f"{value}{unit}") == expected_ms

    def test_expected_examples(self) -> None:
        """The canonical examples from the plan."""
        assert parse_duration("100ms") == 100
        assert parse_duration("2s") == 2_000
        assert parse_duration("1m") == 60_000
        assert parse_duration("1h") == 3_600_000


class TestZeroAndLargeValues:
    """Zero and large numeric values are handled correctly."""

    @pytest.mark.parametrize(
        "input_str",
        ["0ms", "0s", "0m", "0h"],
    )
    def test_zero(self, input_str: str) -> None:
        assert parse_duration(input_str) == 0

    @pytest.mark.parametrize(
        ("input_str", "expected_ms"),
        [
            ("1000000ms", 1_000_000),
            ("86400s", 86_400_000),
            ("1440m", 86_400_000),
            ("24h", 86_400_000),
        ],
    )
    def test_large_values(self, input_str: str, expected_ms: int) -> None:
        assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Formatting tolerance: case-insensitivity and surrounding whitespace
# ---------------------------------------------------------------------------


class TestCaseInsensitivity:
    """Unit suffix matching is case-insensitive."""

    @pytest.mark.parametrize(
        ("input_str", "expected_ms"),
        [
            ("1MS", 1),
            ("2S", 2_000),
            ("3M", 180_000),
            ("4H", 14_400_000),
            ("5mS", 5),
            ("6Ms", 6),
            ("100Ms", 100),
            ("1s", 1_000),
        ],
    )
    def test_mixed_case(self, input_str: str, expected_ms: int) -> None:
        assert parse_duration(input_str) == expected_ms


class TestSurroundingWhitespace:
    """Leading and trailing whitespace is stripped before parsing."""

    @pytest.mark.parametrize(
        ("input_str", "expected_ms"),
        [
            ("  100ms  ", 100),
            ("\t2s\n", 2_000),
            (" 1m ", 60_000),
            ("  1h  ", 3_600_000),
        ],
    )
    def test_whitespace_stripped(self, input_str: str, expected_ms: int) -> None:
        assert parse_duration(input_str) == expected_ms


class TestDecimalValues:
    """Decimal numeric values are converted and rounded to int milliseconds."""

    @pytest.mark.parametrize(
        ("input_str", "expected_ms"),
        [
            ("1.5s", 1_500),
            ("0.5s", 500),
            ("1.25m", 75_000),
            ("0.5h", 1_800_000),
            ("1.15s", 1_150),  # floating-point safe via round()
        ],
    )
    def test_decimal_conversion(self, input_str: str, expected_ms: int) -> None:
        assert parse_duration(input_str) == expected_ms


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


class TestNonStringInput:
    """Non-string inputs raise ``ValueError``."""

    @pytest.mark.parametrize(
        "bad_input",
        [100, None, 1.5, [], {}, (), object(), True],
    )
    def test_raises_value_error(self, bad_input: object) -> None:
        with pytest.raises(ValueError, match="must be a string"):
            parse_duration(bad_input)  # type: ignore[arg-type]


class TestEmptyInput:
    """Empty or whitespace-only strings raise ``ValueError``."""

    @pytest.mark.parametrize(
        "empty",
        ["", "   ", "\t", "\n", "\t\n ", "   \t   "],
    )
    def test_raises_value_error(self, empty: str) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_duration(empty)


class TestMalformedInput:
    """Malformed strings that do not match ``<number><unit>`` raise."""

    @pytest.mark.parametrize(
        "malformed",
        [
            "1",  # number without unit
            "ms",  # unit without number
            "100",  # number without unit
            "1 sec",  # space between number and unit
            "sec",  # unit without number
            "abc",  # pure text
            "1.5",  # decimal without unit
            "--",  # garbage
            "1.",  # number with trailing dot, no unit
            "+",  # sign only
            "1 2s",  # number, space, then valid duration
            "s1",  # reversed order
        ],
    )
    def test_raises_value_error(self, malformed: str) -> None:
        with pytest.raises(ValueError, match="invalid duration"):
            parse_duration(malformed)


class TestCompoundDurations:
    """Compound durations (multiple values/units) are rejected."""

    @pytest.mark.parametrize(
        "compound",
        [
            "1s2s",
            "1m30s",
            "1h30m",
            "1ms2ms",
            "2h15m30s",
            "100ms200ms",
        ],
    )
    def test_raises_value_error(self, compound: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(compound)


class TestUnsupportedUnits:
    """Units outside the supported set (ms, s, m, h) are rejected."""

    @pytest.mark.parametrize(
        "unsupported",
        [
            "1d",
            "1y",
            "1sec",
            "1min",
            "1hr",
            "1w",
            "1ns",
            "1us",
            "1days",
        ],
    )
    def test_raises_value_error(self, unsupported: str) -> None:
        with pytest.raises(ValueError, match="unsupported duration unit"):
            parse_duration(unsupported)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


class TestReturnType:
    """``parse_duration`` returns an ``int``, not a float."""

    def test_returns_int(self) -> None:
        result = parse_duration("100ms")
        assert isinstance(result, int)
        assert not isinstance(result, float)

    def test_decimal_returns_int(self) -> None:
        result = parse_duration("1.5s")
        assert isinstance(result, int)
        assert result == 1_500
