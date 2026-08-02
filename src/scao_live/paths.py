"""Path safety utilities for the SCOA live test package."""

import os


def safe_join(base, *parts):
    """Join ``base`` with ``parts``, preventing path traversal.

    The function joins via :func:`os.path.join`, resolves both the base
    and the candidate with :func:`os.path.realpath` (which follows
    symlinks and normalises separators), and raises :class:`ValueError`
    whenever:

    * any supplied component is not a string;
    * any supplied component contains a ``..`` path segment;
    * the resolved candidate escapes the resolved base (this catches
      absolute-part overrides and symlink escapes that were not caught
      by the explicit ``..`` check).

    When no parts are supplied the resolved base is returned, preserving
    the empty-part behaviour of :func:`os.path.join`.
    """
    # --- type check -------------------------------------------------
    for part in parts:
        if not isinstance(part, str):
            raise ValueError(
                "Path component must be a string, got "
                f"{type(part).__name__}: {part!r}"
            )

    # --- reject '..' in any supplied component ----------------------
    # Normalise both POSIX and NT separators so that patterns like
    # 'a\\..\\b' are caught on every platform.
    for part in parts:
        components = part.replace("\\", "/").split("/")
        if ".." in components:
            raise ValueError(
                f"Path component contains '..': {part!r}"
            )

    # --- resolve base (follow symlinks, normalise) ------------------
    resolved_base = os.path.realpath(base)

    # Empty parts → return the resolved base.
    if not parts:
        return resolved_base

    # --- join, resolve candidate, and verify containment ------------
    candidate = os.path.join(resolved_base, *parts)
    resolved_candidate = os.path.realpath(candidate)

    # Use commonpath for a robust containment check that handles
    # edge cases like root ("/") correctly.  commonpath raises
    # ValueError on Windows when paths live on different drives,
    # which also indicates an escape.
    try:
        common = os.path.commonpath([resolved_base, resolved_candidate])
    except ValueError:
        raise ValueError(
            "Resolved path escapes base: "
            f"{resolved_candidate!r} is not within {resolved_base!r}"
        )

    if common != resolved_base:
        raise ValueError(
            "Resolved path escapes base: "
            f"{resolved_candidate!r} is not within {resolved_base!r}"
        )

    return resolved_candidate
