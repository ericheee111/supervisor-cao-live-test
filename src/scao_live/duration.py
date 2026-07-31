"""Duration string parsing utilities.

Provides :func:`parse_duration` for converting short duration strings
(e.g. ``"100ms"``, ``"2h"``) into an integer number of milliseconds.
"""

_SUFFIX_FACTORS = {
    "ms": 1,
    "s": 1000,
    "m": 60000,
    "h": 3600000,
}


def parse_duration(s):
    """Parse a duration string into milliseconds.

    Accepts a numeric prefix followed by exactly one supported suffix:

    =========  ============  ================
    Suffix     Meaning       Conversion factor
    =========  ============  ================
    ``ms``     milliseconds  1
    ``s``      seconds       1000
    ``m``      minutes       60000
    ``h``      hours         3600000
    =========  ============  ================

    The numeric prefix must be a non-negative integer (no fractional
    digits, no leading sign).

    :param str s: Duration string such as ``"100ms"`` or ``"2h"``.
    :returns: Duration in milliseconds as ``int``.
    :raises ValueError: If *s* is empty, malformed, non-integer,
        fractional, sign-invalid, or uses an unsupported unit.
    """
    if not s:
        raise ValueError("duration string must not be empty")

    for suffix in ("ms", "s", "m", "h"):
        if s.endswith(suffix):
            prefix = s[: -len(suffix)]
            if not prefix or not prefix.isdigit():
                raise ValueError(f"invalid duration: {s!r}")
            return int(prefix) * _SUFFIX_FACTORS[suffix]

    raise ValueError(f"unsupported duration unit in: {s!r}")
