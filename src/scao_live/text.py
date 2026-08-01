"""Text utilities for scao-live."""

import re

_WORD_PATTERN = re.compile(r"\S+")


def capitalize_words(s: str) -> str:
    """Capitalize the first character of each whitespace-delimited word.

    Each maximal run of non-whitespace characters is treated as a word.
    The first character of every word is uppercased; the remaining
    characters are left unchanged.  All whitespace between words is
    preserved exactly.

    Args:
        s: The input string.

    Returns:
        A copy of *s* with the first character of each word uppercased.
    """
    return _WORD_PATTERN.sub(
        lambda match: match.group(0)[:1].upper() + match.group(0)[1:], s
    )
