"""Duration string parsing utilities.

Parses human-readable duration strings such as ``"100ms"`` or ``"2s"`` into
integer millisecond values.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ["parse_duration"]

#: Mapping of supported duration units to their millisecond conversion factors.
_UNIT_FACTORS: Final[dict[str, int]] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}

#: Human-readable list of valid units for error messages.
_VALID_UNITS: Final[str] = ", ".join(_UNIT_FACTORS)

#: Strict pattern: digits immediately followed by exactly one supported unit.
_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(\d+)(ms|s|m|h)$")


def parse_duration(s: str) -> int:
    """Parse a duration string into integer milliseconds.

    The input must be a non-empty string consisting of a non-negative integer
    immediately followed by exactly one supported unit (no whitespace, no
    sign, no fractional part).

    Supported units (case-sensitive):

    ======  ===========  ================
    Unit    Factor       Example
    ======  ===========  ================
    ``ms``  1            ``"100ms"`` -> ``100``
    ``s``   1 000        ``"2s"``    -> ``2_000``
    ``m``   60 000       ``"1m"``    -> ``60_000``
    ``h``   3 600 000    ``"1h"``    -> ``3_600_000``
    ======  ===========  ================

    Parameters
    ----------
    s:
        Duration string to parse.

    Returns
    -------
    int
        The duration expressed as a whole number of milliseconds.

    Raises
    ------
    TypeError
        If *s* is not a ``str``.
    ValueError
        If *s* is empty, contains whitespace, lacks a leading numeric
        value, or ends with an unknown or malformed unit suffix.
    """
    if not isinstance(s, str):
        raise TypeError(f"duration must be a string, got {type(s).__name__}")
    if len(s) == 0:
        raise ValueError("duration string must not be empty")

    # Reject any embedded or surrounding whitespace.
    if any(ch.isspace() for ch in s):
        raise ValueError(f"duration string must not contain whitespace: {s!r}")

    match = _PATTERN.match(s)
    if match is not None:
        numeric_str, unit = match.group(1), match.group(2)
        return int(numeric_str) * _UNIT_FACTORS[unit]

    # Regex failed — classify the specific error for a clear message.
    digits = 0
    for ch in s:
        if ch.isdigit():
            digits += 1
        else:
            break

    if digits == 0:
        raise ValueError(f"duration string must start with a numeric value: {s!r}")

    suffix = s[digits:]
    raise ValueError(
        f"unknown duration unit {suffix!r} in {s!r}; expected one of: {_VALID_UNITS}"
    )
