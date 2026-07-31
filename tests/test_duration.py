"""Tests for :func:`scao_live.duration.parse_duration`.

Covers the four required examples (``"100ms"``, ``"2s"``, ``"1m"``,
``"1h"``) and all invalid-input categories: empty strings, whitespace,
missing numeric values, unknown units, and malformed suffixes.
"""

from __future__ import annotations

import pytest

from scao_live.duration import parse_duration

# ---------------------------------------------------------------------------
# Valid inputs — the four required examples plus additional edge cases.
# ---------------------------------------------------------------------------

REQUIRED_EXAMPLES: list[tuple[str, int]] = [
    ("100ms", 100),
    ("2s", 2_000),
    ("1m", 60_000),
    ("1h", 3_600_000),
]

ADDITIONAL_VALID: list[tuple[str, int]] = [
    ("0ms", 0),
    ("0s", 0),
    ("0m", 0),
    ("0h", 0),
    ("999ms", 999),
    ("500ms", 500),
    ("90s", 90_000),
    ("10m", 600_000),
    ("24h", 86_400_000),
    ("3600s", 3_600_000),
    ("60000ms", 60_000),
]


@pytest.mark.parametrize(
    ("value", "expected"),
    REQUIRED_EXAMPLES + ADDITIONAL_VALID,
)
def test_valid_durations(value: str, expected: int) -> None:
    """Valid duration strings return the correct millisecond count."""
    assert parse_duration(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    REQUIRED_EXAMPLES,
    ids=["ms", "s", "m", "h"],
)
def test_required_examples(value: str, expected: int) -> None:
    """The four examples explicitly required by the specification."""
    assert parse_duration(value) == expected


# ---------------------------------------------------------------------------
# Invalid inputs — empty string.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [""])
def test_empty_string_raises(value: str) -> None:
    """An empty string must raise ValueError mentioning 'empty'."""
    with pytest.raises(ValueError, match="empty"):
        parse_duration(value)


# ---------------------------------------------------------------------------
# Invalid inputs — whitespace (embedded, leading, trailing, or sole content).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        " ",
        "   ",
        "\t",
        "\n",
        "\r",
        "100 ms",
        " 100ms",
        "100ms ",
        "100\tms",
        "100\nms",
        "100\rms",
    ],
)
def test_whitespace_raises(value: str) -> None:
    """Strings containing whitespace must raise ValueError."""
    with pytest.raises(ValueError, match="whitespace"):
        parse_duration(value)


# ---------------------------------------------------------------------------
# Invalid inputs — missing numeric value (no leading digits).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "ms",
        "s",
        "m",
        "h",
        "abc",
        "!",
        "-100ms",
        "+100ms",
    ],
)
def test_missing_numeric_value_raises(value: str) -> None:
    """Strings without a leading numeric value must raise ValueError."""
    with pytest.raises(ValueError, match="numeric"):
        parse_duration(value)


# ---------------------------------------------------------------------------
# Invalid inputs — unknown or malformed unit suffix.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "100x",
        "100d",
        "100sec",
        "1min",
        "1hr",
        "100MS",
        "100S",
        "100M",
        "100H",
        "100ms0",
        "1m30s",
        "100mss",
        "1.5s",
        "100",
    ],
)
def test_unknown_or_malformed_unit_raises(value: str) -> None:
    """Strings with an unknown or malformed suffix must raise ValueError."""
    with pytest.raises(ValueError, match="unknown"):
        parse_duration(value)


# ---------------------------------------------------------------------------
# Invalid inputs — non-string types.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [100, None, 1.5, [], object()])
def test_non_string_raises_type_error(value: object) -> None:
    """Non-string input must raise TypeError."""
    with pytest.raises(TypeError):
        parse_duration(value)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Return type contract.
# ---------------------------------------------------------------------------


def test_return_type_is_int() -> None:
    """The function must return a plain ``int``, not a bool or float."""
    result = parse_duration("100ms")
    assert isinstance(result, int)
    assert not isinstance(result, bool)
