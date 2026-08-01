"""Tests for scao_live.text."""

import pytest

from scao_live.text import capitalize_words


def test_capitalize_words_multi_word():
    """Capitalization of a multi-word string uppercases each first letter."""
    assert capitalize_words("hello world") == "Hello World"


def test_capitalize_words_preserves_whitespace():
    """Whitespace separation between words is preserved exactly."""
    assert capitalize_words("hello   world") == "Hello   World"
    assert capitalize_words("one\ttwo\nthree") == "One\tTwo\nThree"


def test_capitalize_words_single_and_empty():
    """Single words, empty strings, and whitespace-only strings."""
    assert capitalize_words("python") == "Python"
    assert capitalize_words("") == ""
    assert capitalize_words("   ") == "   "


@pytest.mark.parametrize(
    "given, expected",
    [
        ("hello world", "Hello World"),
        ("foo bar baz", "Foo Bar Baz"),
        ("  leading", "  Leading"),
        ("trailing  ", "Trailing  "),
        ("already Capital", "Already Capital"),
        ("123abc def", "123abc Def"),
    ],
)
def test_capitalize_words_cases(given, expected):
    assert capitalize_words(given) == expected
