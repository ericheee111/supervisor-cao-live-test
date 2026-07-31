"""Focused unit tests for scao_live.text.capitalize_words."""

from __future__ import annotations

from scao_live.text import capitalize_words


def test_multiple_words():
    assert capitalize_words("hello world") == "Hello World"


def test_repeated_whitespace_preserved():
    assert capitalize_words("hello   world") == "Hello   World"


def test_leading_whitespace_preserved():
    assert capitalize_words("  hello world") == "  Hello World"


def test_trailing_whitespace_preserved():
    assert capitalize_words("hello world  ") == "Hello World  "


def test_leading_and_trailing_whitespace_preserved():
    assert capitalize_words("  hello  world  ") == "  Hello  World  "


def test_empty_input_returns_empty():
    assert capitalize_words("") == ""


def test_only_whitespace_unchanged():
    assert capitalize_words("   \t  \n ") == "   \t  \n "


def test_already_capitalized_unchanged():
    assert capitalize_words("Hello World") == "Hello World"


def test_mixed_case_preserves_tail():
    # Only the first character is uppercased; the rest of each word is kept.
    assert capitalize_words("hELLO wORLD") == "HELLO WORLD"


def test_single_word():
    assert capitalize_words("hello") == "Hello"


def test_single_character_words():
    assert capitalize_words("a b c") == "A B C"


def test_tabs_and_newlines_preserved_as_whitespace():
    assert capitalize_words("hello\tworld\nfoo") == "Hello\tWorld\nFoo"
