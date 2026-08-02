"""Tests for :mod:`scao_live.duration`.

Covers the four canonical conversions, zero and large integer values,
case-insensitive units, surrounding whitespace handling, the ``int`` return
type, and the full set of invalid inputs (decimals, negatives, embedded
whitespace, missing/unknown units, compound values, and non-strings).
"""

import pytest

from scao_live.duration import parse_duration


class TestCanonicalConversions:
    """The four canonical unit -> millisecond conversions."""

    def test_milliseconds(self):
        assert parse_duration("5ms") == 5

    def test_seconds(self):
        assert parse_duration("5s") == 5000

    def test_minutes(self):
        assert parse_duration("5m") == 300_000

    def test_hours(self):
        assert parse_duration("5h") == 18_000_000


class TestZero:
    """Zero is a valid nonnegative integer for every unit."""

    @pytest.mark.parametrize("unit,expected", [
        ("ms", 0),
        ("s", 0),
        ("m", 0),
        ("h", 0),
    ])
    def test_zero(self, unit, expected):
        assert parse_duration("0" + unit) == expected


class TestLargeIntegers:
    """Large integers stay exact (Python ints are arbitrary precision)."""

    def test_large_seconds(self):
        assert parse_duration("1000000s") == 1_000_000_000

    def test_very_large_hours(self):
        assert parse_duration("999999999999h") == 999_999_999_999 * 3_600_000


class TestCaseInsensitiveUnits:
    """Units may appear in any case combination."""

    @pytest.mark.parametrize("text,expected", [
        ("5MS", 5),
        ("5Ms", 5),
        ("5mS", 5),
        ("5S", 5000),
        ("5M", 300_000),
        ("5H", 18_000_000),
    ])
    def test_case_variants(self, text, expected):
        assert parse_duration(text) == expected


class TestSurroundingWhitespace:
    """Leading/trailing whitespace is stripped before matching."""

    def test_leading_and_trailing_spaces(self):
        assert parse_duration("  5s  ") == 5000

    def test_tabs_and_newlines(self):
        assert parse_duration("\t5s\n") == 5000

    def test_whitespace_only_is_invalid(self):
        with pytest.raises(ValueError):
            parse_duration("   ")


class TestReturnType:
    """The result is always a plain ``int`` (not ``bool``)."""

    def test_returns_int_for_ms(self):
        result = parse_duration("5ms")
        assert isinstance(result, int)

    def test_returns_int_not_bool(self):
        result = parse_duration("1s")
        assert isinstance(result, int)
        assert not isinstance(result, bool)


class TestInvalidStrings:
    """Malformed string inputs must raise ``ValueError``."""

    @pytest.mark.parametrize("value", [
        "5.5s",       # decimal value
        "-5s",        # negative value
        "5 s",        # embedded whitespace between number and unit
        "5",          # missing unit
        "5x",         # unknown unit
        "1m30s",      # compound value
        "5sec",       # extra trailing letters after a valid unit
        "",           # empty string
        "ms",         # no integer
        "5ms5s",      # doubled value
        "+5s",        # leading plus sign
        " 5 s ",      # embedded whitespace surviving the strip
        "5 m",        # space before unit
    ])
    def test_invalid_string_raises(self, value):
        with pytest.raises(ValueError):
            parse_duration(value)


class TestNonStrings:
    """Every non-string input must raise ``ValueError``."""

    @pytest.mark.parametrize("value", [
        None,
        123,
        1.5,
        [],
        {},
        True,
        b"5s",
    ])
    def test_non_string_raises(self, value):
        with pytest.raises(ValueError):
            parse_duration(value)
