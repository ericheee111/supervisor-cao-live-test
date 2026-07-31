"""Tests for :func:`scao_live.duration.parse_duration`."""

from __future__ import annotations

import pytest

from scao_live.duration import parse_duration


# ---------------------------------------------------------------------------
# Valid inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected_ms",
    [
        # The four required examples.
        ("100ms", 100),
        ("2s", 2_000),
        ("3m", 180_000),
        ("1h", 3_600_000),
    ],
    ids=["100ms", "2s", "3m", "1h"],
)
def test_required_examples(raw: str, expected_ms: int) -> None:
    """The four documented examples must produce exact millisecond values."""
    assert parse_duration(raw) == expected_ms


@pytest.mark.parametrize(
    "raw, expected_ms",
    [
        ("0ms", 0),
        ("0s", 0),
        ("0m", 0),
        ("0h", 0),
        ("1ms", 1),
        ("1s", 1_000),
        ("1m", 60_000),
        ("1h", 3_600_000),
        # Larger values stay exact thanks to integer arithmetic.
        ("999999ms", 999_999),
        ("999999s", 999_999_000),
        ("999999m", 59_999_940_000),
        ("999999h", 3_599_996_400_000),
    ],
)
def test_additional_valid_inputs(raw: str, expected_ms: int) -> None:
    """Edge values and large integers are handled without precision loss."""
    assert parse_duration(raw) == expected_ms


def test_ms_does_not_collide_with_s() -> None:
    """``"100ms"`` must be parsed as milliseconds, not 100 followed by ``s``.

    This guards the unit-ordering invariant (``ms`` checked before ``s``).
    """
    assert parse_duration("100ms") == 100
    assert parse_duration("100s") == 100_000


def test_return_type_is_int() -> None:
    """All results are plain Python ``int`` (no float leakage)."""
    for raw in ("100ms", "2s", "3m", "1h"):
        result = parse_duration(raw)
        assert isinstance(result, int)
        assert not isinstance(result, float)


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, reason",
    [
        # Empty string.
        ("", "empty"),
        # Unknown units.
        ("100x", "unknown unit"),
        ("100sec", "unknown unit"),
        ("100min", "unknown unit"),
        ("100hr", "unknown unit"),
        # Missing unit entirely.
        ("100", "missing unit"),
        # Non-numeric value before a valid unit.
        ("abcms", "non-numeric"),
        ("xs", "non-numeric"),
        ("ms", "no number before unit"),
        ("s", "no number before unit"),
        ("m", "no number before unit"),
        ("h", "no number before unit"),
        # Float-looking values are not integer arithmetic.
        ("1.5s", "float numeric"),
        # Number followed by extra letters before the unit.
        ("100sms", "non-numeric"),
        ("1h2s", "non-numeric"),
    ],
)
def test_invalid_inputs_raise_value_error(raw: str, reason: str) -> None:
    """Every malformed input must raise ``ValueError`` with a clear message."""
    with pytest.raises(ValueError, match=raw if raw else "empty"):
        parse_duration(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "100 ms",      # interior space
        " 100ms",      # leading space
        "100ms ",      # trailing space
        "100\tms",     # interior tab
        " 100ms ",     # surrounding spaces
        "100\nms",     # interior newline
    ],
)
def test_whitespace_is_rejected(raw: str) -> None:
    """Strings containing any whitespace character must be rejected."""
    with pytest.raises(ValueError, match="whitespace"):
        parse_duration(raw)


@pytest.mark.parametrize(
    "raw",
    [
        # Uppercase units are rejected (case-sensitive matching).
        "100MS",
        "100S",
        "100M",
        "100H",
        # Mixed case is also rejected.
        "100Ms",
        "100mS",
        "100Hs",
    ],
)
def test_case_sensitive_units_rejected(raw: str) -> None:
    """Only lowercase units are accepted; any other case is an error."""
    with pytest.raises(ValueError, match=raw if raw else "empty"):
        parse_duration(raw)


def test_non_string_input_rejected() -> None:
    """Non-string inputs must raise ``ValueError`` rather than ``TypeError``."""
    for bad in (None, 100, 1.5, b"100ms", ["100ms"], object()):
        with pytest.raises(ValueError, match="must be a string"):
            parse_duration(bad)  # type: ignore[arg-type]


def test_error_messages_are_descriptive() -> None:
    """Error messages should name the offending input for easy debugging."""
    # Empty -> mentions empty.
    with pytest.raises(ValueError, match="empty"):
        parse_duration("")

    # Whitespace -> mentions whitespace.
    with pytest.raises(ValueError, match="whitespace"):
        parse_duration("100 ms")

    # Unknown unit -> mentions unknown/missing unit.
    with pytest.raises(ValueError, match="unknown|missing"):
        parse_duration("100x")

    # Non-numeric -> mentions non-integer.
    with pytest.raises(ValueError, match="non-integer|non-numeric"):
        parse_duration("abcs")
