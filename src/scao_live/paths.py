"""Safe path-joining utilities for Supervisor-CAO live components.

This module provides :func:`safe_join`, a helper that joins filesystem
paths while rejecting components that would escape the intended base
directory.  It is intended for use in agent orchestration code where
untrusted path fragments must be confined to a known sandbox.
"""

from __future__ import annotations

import os

__all__ = ["safe_join"]


def safe_join(base: str, *parts: str) -> str:
    """Join *parts* under *base*, rejecting traversal and absolute escapes.

    The function accepts empty parts and normalises the result, but
    raises :class:`ValueError` when a part is an absolute path, when a
    part is exactly ``".."``, or when the normalised joined path falls
    outside the normalised base directory.

    Parameters
    ----------
    base:
        The base directory that the result must remain within.
    parts:
        Additional path components to join under *base*.  Empty
        strings are accepted and effectively ignored after
        normalisation.

    Returns
    -------
    str
        The normalised joined path, guaranteed to be within *base*.

    Raises
    ------
    ValueError
        If any part is an absolute path, equals ``".."``, or the
        joined result normalises to a path outside *base*.
    """
    for part in parts:
        # ``os.path.isabs`` catches drive-letter absolute paths on Windows
        # (e.g. ``C:\\Windows``) and all absolute paths on POSIX.
        #
        # On Python 3.14+ on Windows ``os.path.isabs`` no longer treats a
        # leading ``/`` or ``\\`` as absolute, yet ``os.path.join`` still
        # discards the base when it encounters such a component.  Check
        # explicitly for a leading separator so the part is rejected with
        # an informative message rather than falling through to the
        # containment check.
        if (
            os.path.isabs(part)
            or part.startswith(os.sep)
            or (os.altsep is not None and part.startswith(os.altsep))
        ):
            raise ValueError(f"absolute path component not allowed: {part!r}")
        if part == "..":
            raise ValueError("parent traversal component '..' is not allowed")

    joined = os.path.join(base, *parts) if parts else base
    normalized = os.path.normpath(joined)
    normalized_base = os.path.normpath(base)

    # Use abspath for the containment check so that relative bases
    # (including "." or "") are resolved consistently against the
    # current working directory.  The *return value* is the relative
    # normalised path, not the absolute one.
    abs_result = os.path.abspath(normalized)
    abs_base = os.path.abspath(normalized_base)

    if abs_result != abs_base and not abs_result.startswith(abs_base + os.sep):
        raise ValueError(f"joined path {normalized!r} escapes base {normalized_base!r}")

    return normalized
