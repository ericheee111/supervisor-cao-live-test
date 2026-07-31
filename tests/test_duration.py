"""Focused tests for :func:`scao_live.duration.parse_duration`."""

from __future__ import annotations

import pytest

from scao_live.duration import DurationParseError, parse_duration

# ---------------------------------------------------------------------------
# Valid inputs
# ---------------------------------------------------------------------------

class TestValidDurations:
    @pytest.mark.parametrize(
        "text, expected_ms",
        [
            # milliseconds
            ("0ms", 0),
            ("1ms", 1),
            ("100ms", 100),
            ("500ms", 500),
            # seconds
            ("0s", 0),
            ("1s", 1_000),
            ("5s", 5_000),
            ("30s", 30_000),
            ("60s", 60_000),
            # minutes
            ("0m", 0),
            ("1m", 60_000),
            ("2m", 120_000),
            ("10m", 600_000),
            # hours
            ("0h", 0),
            ("1h", 3_600_000),
            ("2h", 7_200_000),
            ("24h", 86_400_000),
        ],
    )
    def test_all_units(self, text, expected_ms):
        assert parse_duration(text) == expected_ms

    @pytest.mark.parametrize(
        "text, expected_ms",
        [
            ("  5s  ", 5_000),
            (" 1ms", 1),
            ("100ms   ", 100),
            ("\t3m\n", 180_000),
            ("  0h  ", 0),
        ],
    )
    def test_whitespace_trimmed(self, text, expected_ms):
        assert parse_duration(text) == expected_ms

    def test_zero(self):
        assert parse_duration("0ms") == 0
        assert parse_duration("0s") == 0
        assert parse_duration("0m") == 0
        assert parse_duration("0h") == 0

    def test_leading_zeros(self):
        assert parse_duration("007s") == 7_000

    def test_large_value(self):
        assert parse_duration("1000000ms") == 1_000_000

    def test_returns_int(self):
        result = parse_duration("5s")
        assert isinstance(result, int)
        assert result == 5_000


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

class TestInvalidDurations:
    @pytest.mark.parametrize(
        "text",
        [
            "",            # empty string
            "   ",         # whitespace only
            "\t\n",        # whitespace only
            "s",           # missing number
            "ms",          # missing number
            "m",           # missing number
            "h",           # missing number
            "5",           # missing unit
            "10",          # missing unit
            "5S",          # uppercase unit
            "5MS",         # uppercase unit
            "5H",          # uppercase unit
            "5M",          # uppercase unit
            "5x",          # unknown unit
            "5sec",        # unknown unit
            "5min",        # unknown unit
            "-5s",         # negative
            "-1ms",        # negative
            "-1h",         # negative
            "1.5s",        # decimal
            "0.5ms",       # decimal
            "2.0h",        # decimal
            "5 s",         # internal space
            "5 ms",        # internal space
            "abc",         # no digits at all
            "5m5s",        # compound / trailing characters
            "5ms5",        # trailing characters after valid unit
        ],
    )
    def test_invalid_string_raises(self, text):
        with pytest.raises(DurationParseError):
            parse_duration(text)

    @pytest.mark.parametrize(
        "value",
        [None, 5, 5.0, True, False, [], {}, object()],
    )
    def test_non_string_raises(self, value):
        with pytest.raises(DurationParseError):
            parse_duration(value)

    def test_error_is_value_error(self):
        with pytest.raises(ValueError):
            parse_duration("")

    def test_non_string_message_contains_type_name(self):
        with pytest.raises(DurationParseError, match="int"):
            parse_duration(5)

    def test_empty_message_mentions_empty(self):
        with pytest.raises(DurationParseError, match="empty"):
            parse_duration("")

    def test_missing_unit_message(self):
        with pytest.raises(DurationParseError, match="unit"):
            parse_duration("5")

    def test_unknown_unit_message(self):
        with pytest.raises(DurationParseError, match="unsupported"):
            parse_duration("5x")

    def test_missing_number_message(self):
        with pytest.raises(DurationParseError, match="nonnegative integer"):
            parse_duration("s")
