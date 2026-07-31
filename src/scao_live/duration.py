"""Duration parsing utility for the scao_live package.

Provides :func:`parse_duration`, which converts a human-readable duration
string (a nonnegative integer followed by a lowercase unit) into an
integer number of milliseconds.
"""

from __future__ import annotations

__all__ = ["DurationParseError", "parse_duration"]


class DurationParseError(ValueError):
    """Raised when a duration string cannot be parsed."""


# Fixed conversion factors to milliseconds.
_UNITS_TO_MS: dict[str, int] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}


def parse_duration(s: str) -> int:
    """Parse a duration string into milliseconds.

    The accepted format is a nonnegative integer immediately followed by
    one of the lowercase units ``ms``, ``s``, ``m``, or ``h``.
    Surrounding whitespace is trimmed before parsing.

    Parameters
    ----------
    s:
        Duration string such as ``"500ms"``, ``"30s"``, ``"5m"``, or
        ``"2h"``.

    Returns
    -------
    int
        The duration in milliseconds.

    Raises
    ------
    DurationParseError
        If *s* is not a string, is empty, is missing a number or unit,
        contains a negative or decimal value, or uses an unsupported
        unit.
    """
    if not isinstance(s, str):
        raise DurationParseError(f"expected a string, got {type(s).__name__}")

    text = s.strip()
    if not text:
        raise DurationParseError("duration string is empty")

    # Scan leading digits to separate the numeric part from the unit.
    digits_end = 0
    for ch in text:
        if ch.isdigit():
            digits_end += 1
        else:
            break

    if digits_end == 0:
        raise DurationParseError(
            f"duration must start with a nonnegative integer: {s!r}"
        )

    number_str = text[:digits_end]
    unit = text[digits_end:]

    if not unit:
        raise DurationParseError(f"duration is missing a unit: {s!r}")

    if unit not in _UNITS_TO_MS:
        raise DurationParseError(
            f"unsupported unit {unit!r}; expected one of {sorted(_UNITS_TO_MS)}"
        )

    # int() handles leading zeros; the value is guaranteed nonnegative
    # because only digit characters were accepted.
    return int(number_str) * _UNITS_TO_MS[unit]
