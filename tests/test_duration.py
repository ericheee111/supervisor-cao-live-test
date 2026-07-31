"""Tests for :func:`scao_live.duration.parse_duration`."""

from __future__ import annotations

from typing import cast

import pytest

from scao_live.duration import parse_duration


class TestRequiredConversions:
    """The four required unit conversions and integer return type."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("100ms", 100),
            ("2s", 2_000),
            ("1m", 60_000),
            ("1h", 3_600_000),
        ],
    )
    def test_unit_conversions(self, raw: str, expected: int) -> None:
        assert parse_duration(raw) == expected

    def test_returns_int(self) -> None:
        assert isinstance(parse_duration("100ms"), int)
        assert isinstance(parse_duration("0s"), int)


class TestZeroValues:
    """Zero amounts yield zero milliseconds for every supported unit."""

    @pytest.mark.parametrize("raw", ["0ms", "0s", "0m", "0h"])
    def test_zero_returns_zero(self, raw: str) -> None:
        assert parse_duration(raw) == 0


class TestWhitespacePolicy:
    """Surrounding whitespace is stripped; internal whitespace is rejected."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("  100ms", 100),
            ("100ms  ", 100),
            ("  100ms  ", 100),
            ("\t2s\n", 2_000),
        ],
    )
    def test_surrounding_whitespace_stripped(self, raw: str, expected: int) -> None:
        assert parse_duration(raw) == expected

    @pytest.mark.parametrize("raw", ["   ", "\t\t", ""])
    def test_empty_or_whitespace_only_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)

    @pytest.mark.parametrize("raw", ["100 ms", "1 0 0ms", "1m 2s"])
    def test_internal_whitespace_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)


class TestInvalidInputs:
    """Missing units, unsupported/uppercase units, and non-numeric prefixes."""

    @pytest.mark.parametrize("raw", ["100", "ms", "1", "h"])
    def test_missing_unit_or_value_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)

    @pytest.mark.parametrize("raw", ["100d", "100y", "100ns", "100sec"])
    def test_unsupported_units_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)

    @pytest.mark.parametrize("raw", ["100MS", "100S", "100M", "100H", "100Ms"])
    def test_uppercase_units_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)

    @pytest.mark.parametrize("raw", ["abcs", "tenms", "1.5s", "1.2.3s", "--1s"])
    def test_non_numeric_prefix_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_duration(raw)

    @pytest.mark.parametrize("raw", [None, 100, 1.5, [], object()])
    def test_non_string_input_rejected(self, raw: object) -> None:
        with pytest.raises(TypeError):
            parse_duration(cast(str, raw))
