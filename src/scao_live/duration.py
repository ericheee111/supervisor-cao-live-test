"""Duration string parsing utilities.

Provides :func:`parse_duration` for converting human-readable duration
strings (e.g. ``"5s"``, ``"100ms"``) into an integer number of
milliseconds.
"""

from __future__ import annotations

import re

__all__ = ["parse_duration"]

_PATTERN = re.compile(r"^(\d+)(ms|s|m|h)$", re.IGNORECASE)

_MULTIPLIERS: dict[str, int] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}


def parse_duration(s: str) -> int:
    """Parse a duration string into milliseconds.

    The input must be a nonnegative integer immediately followed by one
    of the unit suffixes ``ms``, ``s``, ``m``, or ``h`` (case-insensitive).
    Surrounding whitespace is ignored.

    Parameters
    ----------
    s:
        Duration string to parse.

    Returns
    -------
    int
        The duration in milliseconds.

    Raises
    ------
    ValueError
        If *s* is empty, malformed, contains combined units (e.g.
        ``"1h30m"``), is negative, contains a decimal, or uses an
        unknown unit.
    """
    stripped = s.strip()
    if not stripped:
        raise ValueError("duration string must not be empty")
    match = _PATTERN.match(stripped)
    if match is None:
        raise ValueError(f"invalid duration string: {s!r}")
    value_str, unit = match.groups()
    return int(value_str) * _MULTIPLIERS[unit.lower()]
