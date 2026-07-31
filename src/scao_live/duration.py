"""Duration string parsing utilities.

Provides :func:`parse_duration` for converting a duration string such as
``"500ms"`` or ``"2s"`` into an integer number of milliseconds.
"""

from __future__ import annotations

import re

__all__ = ["parse_duration"]

_UNIT_FACTORS: dict[str, int] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}

_PATTERN = re.compile(r"^(\d+)(ms|s|m|h)$")


def parse_duration(s: str) -> int:
    """Parse a duration string into milliseconds.

    The expected format is a single nonnegative integer immediately
    followed by one of the unit suffixes ``ms``, ``s``, ``m``, or ``h``.

    Args:
        s: Duration string such as ``"500ms"`` or ``"2s"``.

    Returns:
        The duration in milliseconds as an integer.

    Raises:
        ValueError: If *s* is empty, malformed, negative, or uses an
            unsupported unit.
    """
    match = _PATTERN.match(s)
    if match is None:
        raise ValueError(f"malformed duration: {s!r}")
    value, unit = match.group(1), match.group(2)
    return int(value) * _UNIT_FACTORS[unit]
