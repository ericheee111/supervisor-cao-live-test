def parse_int(s):
    """Parse a string to int. Raises ValueError for empty input."""
    if not s:
        raise ValueError("empty string is not a valid integer")
    return int(s)
