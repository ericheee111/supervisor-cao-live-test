"""Duration string parsing utilities.

:func:`parse_duration` converts a human-readable duration string such as
``"100ms"`` or ``"2s"`` into an integer number of milliseconds.
"""

from __future__ import annotations

import re

__all__ = ["parse_duration"]

#: Multiplier mapping each supported unit to its equivalent milliseconds.
_UNIT_TO_MILLIS: dict[str, int] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}

#: ``ms`` is listed before ``s``/``m`` so the regex does not stop at a
#: single-character unit when the input actually carries ``ms``.
_DURATION_PATTERN = re.compile(
    r"^(?P<value>\d+)(?P<unit>ms|s|m|h)$",
)


def parse_duration(value: str) -> int:
    """Parse a duration string into integer milliseconds.

    Supported units (case-sensitive, lowercase only):

    * ``ms`` -- milliseconds (multiplier ``1``)
    * ``s``  -- seconds      (multiplier ``1_000``)
    * ``m``  -- minutes      (multiplier ``60_000``)
    * ``h``  -- hours        (multiplier ``3_600_000``)

    The numeric prefix must be a non-negative integer (one or more digits).
    Leading and trailing whitespace is tolerated and stripped, mirroring the
    behaviour of the built-in :func:`int` and :func:`float` constructors.
    Internal whitespace, missing units, unsupported or uppercase units, empty
    strings, and non-numeric prefixes are rejected.

    Args:
        value: Duration string such as ``"100ms"``, ``"2s"``, ``"1m"`` or
            ``"1h"``.

    Returns:
        The equivalent number of milliseconds as an :class:`int`.

    Raises:
        TypeError: If *value* is not a string.
        ValueError: If *value* is empty or whitespace-only, or does not
            match the ``<digits><unit>`` grammar.
    """
    if not isinstance(value, str):
        raise TypeError(f"parse_duration expects a str, got {type(value).__name__}")

    stripped = value.strip()
    if not stripped:
        raise ValueError("duration string must not be empty")

    match = _DURATION_PATTERN.match(stripped)
    if match is None:
        raise ValueError(f"invalid duration string: {value!r}")

    amount = int(match.group("value"))
    return amount * _UNIT_TO_MILLIS[match.group("unit")]
