"""Text utilities for scao_live."""


def capitalize_words(s: str) -> str:
    """Capitalize each whitespace-delimited word in *s*.

    The input is normalised by splitting on arbitrary runs of whitespace
    (via :meth:`str.split` with no arguments), each resulting word is
    capitalised with :meth:`str.capitalize`, and the words are rejoined
    with single spaces.

    Examples:
        >>> capitalize_words("hello world")
        'Hello World'
        >>> capitalize_words("  multiple   spaces  ")
        'Multiple Spaces'
        >>> capitalize_words("")
        ''
    """
    return " ".join(word.capitalize() for word in s.split())
