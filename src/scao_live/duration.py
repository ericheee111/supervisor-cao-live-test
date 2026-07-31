"""Duration string parsing for scao_live.

Converts human-friendly duration strings (e.g. ``"100ms"``, ``"2s"``) into
integer milliseconds using pure integer arithmetic.
"""

from __future__ import annotations

# (unit_suffix, multiplier_to_milliseconds)
# ``ms`` must be checked before ``s`` because ``"ms"`` ends with ``"s"``.
_UNIT_MULTIPLIERS: tuple[tuple[str, int], ...] = (
    ("ms", 1),
    ("s", 1000),
    ("m", 60 * 1000),
    ("h", 60 * 60 * 1000),
)


def parse_duration(s: str) -> int:
    """Parse a numeric duration string into milliseconds.

    Accepted units (case-sensitive, lowercase only)::

        ms  -> milliseconds      (multiply by 1)
        s   -> seconds           (multiply by 1_000)
        m   -> minutes           (multiply by 60_000)
        h   -> hours             (multiply by 3_600_000)

    The numeric portion must be a base-10 integer (``"100"``, ``"2"``,
    ``"0"``).  No floating point, whitespace, or sign prefixes are accepted
    beyond what :func:`int` itself tolerates; all arithmetic is performed
    with Python ``int`` values so there is no precision loss.

    Args:
        s: Duration string such as ``"100ms"``, ``"2s"``, ``"3m"``,
            ``"1h"``.

    Returns:
        The equivalent number of milliseconds as an ``int``.

    Raises:
        ValueError: If *s* is empty, contains whitespace, uses an
            unknown or wrong-case unit, or has a non-integer numeric
            portion.

    Examples:
        >>> parse_duration("100ms")
        100
        >>> parse_duration("2s")
        2000
        >>> parse_duration("3m")
        180000
        >>> parse_duration("1h")
        3600000
    """
    if not isinstance(s, str):
        raise ValueError(
            f"duration must be a string, got {type(s).__name__}: {s!r}"
        )

    if len(s) == 0:
        raise ValueError("duration string must not be empty")

    if any(ch.isspace() for ch in s):
        raise ValueError(
            f"duration string must not contain whitespace: {s!r}"
        )

    for unit, multiplier in _UNIT_MULTIPLIERS:
        if s.endswith(unit):
            number_part = s[: -len(unit)]
            if len(number_part) == 0:
                raise ValueError(
                    f"duration string has no numeric value before unit "
                    f"{unit!r}: {s!r}"
                )
            # ``int`` rejects floats, letters, and stray punctuation with
            # a ValueError of its own; we re-wrap it with a clearer message.
            try:
                value = int(number_part)
            except ValueError:
                raise ValueError(
                    f"duration string has non-integer numeric value "
                    f"{number_part!r} before unit {unit!r}: {s!r}"
                ) from None
            return value * multiplier

    raise ValueError(
        f"duration string has unknown or missing unit "
        f"(expected one of ms, s, m, h): {s!r}"
    )
