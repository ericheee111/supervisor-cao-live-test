"""Duration parsing utilities for scao_live.

``parse_duration`` accepts a string of the form ``<integer><unit>`` where the
unit is one of ``ms``, ``s``, ``m`` or ``h`` (case-insensitive) and returns
the duration in milliseconds as an ``int``. Surrounding whitespace is stripped;
every other invalid input -- including non-strings -- raises ``ValueError``.
"""

import re

__all__ = ["parse_duration"]

# A nonnegative integer (digits only) immediately followed by a unit.
# ``fullmatch`` is used so that no trailing characters (including stray
# newlines) are tolerated after the unit.
_UNIT_RE = re.compile(r"(\d+)(ms|s|m|h)", re.IGNORECASE)

# Integer conversion factors to milliseconds. ``ms`` is the smallest unit so
# every conversion is exact and yields an ``int``.
_FACTORS = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}


def parse_duration(s: str) -> int:
    """Parse a duration string into milliseconds.

    The accepted form is, after stripping surrounding whitespace::

        <nonnegative-integer><unit>

    where ``<unit>`` is one of ``ms``, ``s``, ``m`` or ``h`` (case-insensitive)
    and must follow the integer immediately with no characters in between.

    Args:
        s: The duration string to parse.

    Returns:
        The integer number of milliseconds represented by ``s``.

    Raises:
        ValueError: If ``s`` is not a string, is empty, contains a decimal,
            a negative value, embedded whitespace between the integer and the
            unit, a missing or unknown unit, a compound value, or any other
            malformed input.
    """
    if not isinstance(s, str):
        raise ValueError(
            f"duration must be a string, got {type(s).__name__}"
        )

    stripped = s.strip()
    match = _UNIT_RE.fullmatch(stripped)
    if match is None:
        raise ValueError(f"invalid duration: {s!r}")

    value = int(match.group(1))
    unit = match.group(2).lower()
    return value * _FACTORS[unit]
