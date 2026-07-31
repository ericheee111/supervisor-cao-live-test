"""Text utilities for scao_live."""

from __future__ import annotations

import re

__all__ = ["capitalize_words"]

# Matches a maximal run of non-whitespace characters (a "word").
# Whitespace between words is left untouched by re.sub because only the
# non-whitespace spans are replaced.
_WORD_RE = re.compile(r"\S+")


def capitalize_words(s: str) -> str:
    """Return *s* with the first character of each whitespace-delimited word
    uppercased, preserving the remaining characters of each word and all
    original whitespace.

    Examples:
        >>> capitalize_words("hello world")
        'Hello World'
        >>> capitalize_words("hello   world")
        'Hello   World'
        >>> capitalize_words("")
        ''
        >>> capitalize_words("hELLO")
        'HELLO'
    """
    return _WORD_RE.sub(
        lambda match: match.group(0)[:1].upper() + match.group(0)[1:],
        s,
    )
