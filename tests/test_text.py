"""Tests for scao_live.text.capitalize_words."""

from scao_live.text import capitalize_words


def test_normal_sentence():
    """A typical lowercase sentence is capitalized word-by-word."""
    assert capitalize_words("hello world") == "Hello World"


def test_empty_input():
    """An empty string returns an empty string."""
    assert capitalize_words("") == ""


def test_repeated_and_surrounding_whitespace():
    """Runs of spaces, tabs and newlines are collapsed to single spaces."""
    assert capitalize_words("  multiple   spaces  ") == "Multiple Spaces"
    assert capitalize_words("\thello\t\tworld\t") == "Hello World"
    assert capitalize_words("\n\nhello\n\n\nworld\n") == "Hello World"


def test_single_word():
    """A single word is capitalized with no extra spacing."""
    assert capitalize_words("python") == "Python"


def test_punctuation():
    """Words beginning with punctuation are handled by str.capitalize rules."""
    # str.capitalize lowercases the tail and uppercases the first *character*.
    # A leading punctuation char is already non-alphabetic, so it stays as-is
    # and the following alphabetic character is lowercased.
    assert capitalize_words('"hello" "world"') == '"hello" "world"'
    assert capitalize_words("(hello) (world)") == "(hello) (world)"


def test_numeric_and_non_alphabetic_leading_characters():
    """Words whose first character is non-alphabetic keep it unchanged and
    the rest of the word is lowercased by str.capitalize."""
    assert capitalize_words("123abc 456def") == "123abc 456def"
    assert capitalize_words("3.14 2x4") == "3.14 2x4"
    assert capitalize_words("_foo _bar") == "_foo _bar"


def test_already_capitalized_input_is_normalised():
    """All-caps input is lowercased in the tail by str.capitalize."""
    assert capitalize_words("HELLO WORLD") == "Hello World"


def test_mixed_case_and_whitespace():
    """Mixed-case words with irregular whitespace are normalised."""
    assert capitalize_words("  hELLo   wORLd  ") == "Hello World"
