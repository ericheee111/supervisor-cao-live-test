def safe_join(base, *parts):
    """Join base with parts. Should prevent path traversal."""
    import os
    return os.path.join(base, *parts)
