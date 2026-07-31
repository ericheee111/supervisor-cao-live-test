"""Tests for :func:`scao_live.duration.parse_duration`."""

import pytest

from scao_live.duration import parse_duration


# ---------------------------------------------------------------------------
# Valid inputs — all four suffixes
# ---------------------------------------------------------------------------

class TestValidSuffixes:
    """All four supported suffixes parse to the correct millisecond count."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("100ms", 100),
            ("5s", 5_000),
            ("2m", 120_000),
            ("1h", 3_600_000),
        ],
    )
    def test_suffix(self, value, expected):
        assert parse_duration(value) == expected


# ---------------------------------------------------------------------------
# Integer numeric-prefix parsing
# ---------------------------------------------------------------------------

class TestIntegerPrefix:
    """Integer prefixes — including edge cases — parse correctly."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0ms", 0),
            ("1ms", 1),
            ("007s", 7_000),          # leading zeros are valid integers
            ("000ms", 0),
            ("999999ms", 999_999),
            ("60s", 60_000),
            ("60m", 3_600_000),
            ("1000ms", 1_000),
            ("10h", 36_000_000),
        ],
    )
    def test_integer_prefix(self, value, expected):
        assert parse_duration(value) == expected


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    """parse_duration always returns ``int``."""

    @pytest.mark.parametrize("value", ["1ms", "1s", "1m", "1h"])
    def test_returns_int(self, value):
        result = parse_duration(value)
        assert isinstance(result, int)
        assert not isinstance(result, bool)


# ---------------------------------------------------------------------------
# Invalid inputs — must raise ValueError
# ---------------------------------------------------------------------------

class TestInvalidInputs:
    """Malformed, empty, fractional, sign-invalid, and unsupported-unit
    inputs all raise ``ValueError``."""

    @pytest.mark.parametrize(
        ("value", "label"),
        [
            # --- empty ---
            ("", "empty string"),

            # --- malformed: suffix only, no numeric prefix ---
            ("s", "suffix only: s"),
            ("ms", "suffix only: ms"),
            ("m", "suffix only: m"),
            ("h", "suffix only: h"),

            # --- malformed: no suffix at all ---
            ("100", "no suffix"),
            ("1000", "no suffix"),

            # --- malformed: whitespace ---
            (" 5s", "leading whitespace"),
            ("5s ", "trailing whitespace"),
            ("5 s", "internal space"),

            # --- malformed: suffix not at end / prefix after suffix ---
            ("100s5", "digits after suffix"),
            ("s100", "prefix after suffix"),

            # --- fractional ---
            ("1.5s", "fractional seconds"),
            ("0.1ms", "fractional milliseconds"),
            ("0.5h", "fractional hours"),
            ("3.14m", "fractional minutes"),

            # --- sign-invalid ---
            ("-5s", "negative sign"),
            ("+5s", "plus sign"),
            ("-1ms", "negative milliseconds"),
            ("+0s", "plus zero"),

            # --- unsupported unit ---
            ("100x", "unsupported: x"),
            ("100sec", "unsupported: sec"),
            ("100MS", "uppercase MS"),
            ("100S", "uppercase S"),
            ("100M", "uppercase M"),
            ("100H", "uppercase H"),
            ("100d", "unsupported: days"),
            ("100y", "unsupported: years"),
        ],
    )
    def test_raises_value_error(self, value, label):
        with pytest.raises(ValueError):
            parse_duration(value)
