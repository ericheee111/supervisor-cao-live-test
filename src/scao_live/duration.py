"""Duration string parsing utilities for scao-live.

This module provides :func:`parse_duration`, which converts a human-readable
duration string such as ``"100ms"`` or ``"2s"`` into an integer number of
milliseconds.  Only a single numeric value followed by one of the supported
unit suffixes (``ms``, ``s``, ``m``, ``h``) is accepted.  Compound durations
like ``"1m30s"`` are rejected.
"""

from __future__ import annotations

import re
from typing import Final

#: Mapping of supported unit suffix (lowercase) to its millisecond factor.
_UNIT_FACTORS_MS: Final[dict[str, int]] = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}

#: Regex matching a single numeric value followed by a unit suffix.
#:
#: Group 1 captures the numeric value (optional sign, integer or decimal).
#: Group 2 captures the unit suffix (letters only, case-insensitive).
#:
#: The entire string (after whitespace stripping) must match, which rejects
#: compound durations such as ``"1m30s"`` and stray characters such as
#: ``"1 sec"``.
_DURATION_RE: Final[re.Pattern[str]] = re.compile(
    r"^([+-]?(?:\d+\.?\d*|\.\d+))([a-zA-Z]+)$"
)


def parse_duration(s: str) -> int:
    """Parse a duration string into milliseconds.

    The input must be a string containing exactly one numeric value followed
    by one of the case-insensitive unit suffixes ``ms``, ``s``, ``m``, or
    ``h``.  Surrounding whitespace is ignored.

    Parameters
    ----------
    s:
        Duration string such as ``"100ms"``, ``"2s"``, ``"1m"``, or
        ``"1h"``.  Decimal values such as ``"1.5s"`` are accepted.

    Returns
    -------
    int
        The duration expressed in milliseconds.

    Raises
    ------
    ValueError
        If *s* is not a string, is empty after stripping whitespace, does not
        match the ``<number><unit>`` form, uses an unsupported unit, or
        contains additional trailing content (compound durations).

    Examples
    --------
    >>> parse_duration("100ms")
    100
    >>> parse_duration("2s")
    2000
    >>> parse_duration("1m")
    60000
    >>> parse_duration("1h")
    3600000
    """
    if not isinstance(s, str):
        raise ValueError(  # noqa: TRY004 - plan requires ValueError for all invalid inputs
            f"duration must be a string, got {type(s).__name__}: {s!r}"
        )

    stripped = s.strip()
    if not stripped:
        raise ValueError("duration string is empty")

    match = _DURATION_RE.match(stripped)
    if match is None:
        raise ValueError(f"invalid duration {s!r}: expected '<number><unit>'")

    value_text = match.group(1)
    unit_text = match.group(2).lower()

    factor = _UNIT_FACTORS_MS.get(unit_text)
    if factor is None:
        supported = ", ".join(sorted(_UNIT_FACTORS_MS))
        raise ValueError(
            f"unsupported duration unit {unit_text!r} in {s!r}; "
            f"expected one of: {supported}"
        )

    # ``round`` absorbs floating-point representation error (e.g.
    # ``1.15 * 1000`` yielding ``1149.999…``) and returns an ``int`` when
    # called with a single argument, giving a clean integer millisecond count.
    return round(float(value_text) * factor)
