"""Path safety utilities for scao-live.

This module provides :func:`safe_join`, a path joiner that rejects
traversal and absolute-escape attempts before returning a joined path.

The implementation uses :mod:`posixpath` so that path semantics are
consistent regardless of the host operating system.  This matches the
Unix-style paths used throughout the scao-live test fixtures.
"""

from __future__ import annotations

import posixpath
import re

__all__ = ["safe_join"]

# Matches Windows drive-letter absolute paths such as ``C:\\Windows`` or
# ``D:/secret``.  ``posixpath.isabs`` does not recognise these, so they
# are checked separately.
_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def safe_join(base: str, *parts: str) -> str:
    """Join *base* with *parts* while preventing path traversal.

    The function enforces three layers of defence:

    1. **Absolute-component rejection** -- any part that is itself an
       absolute path (Unix ``/etc`` or Windows ``C:\\Windows``) is
       rejected.
    2. **Traversal-component rejection** -- any part whose components
       include ``..`` (whether passed directly as ``..`` or embedded
       inside a multi-segment part such as ``a/../b``) is rejected.
    3. **Normalized-result containment** -- after joining and
       normalizing, the result must still reside inside the normalized
       *base* directory.

    Empty parts are accepted and do not affect the result.

    Parameters:
        base: The base directory to join parts onto.
        *parts: Path components to join under *base*.

    Returns:
        The normalized joined path, guaranteed to be inside *base*.

    Raises:
        ValueError: If any part is unsafe or the normalized result
            escapes *base*.
    """
    if not isinstance(base, str):
        raise TypeError(f"base must be a string, got {type(base).__name__}")

    norm_base = posixpath.normpath(base)

    clean_parts: list[str] = []
    for idx, part in enumerate(parts):
        if not isinstance(part, str):
            raise TypeError(f"part {idx} must be a string, got {type(part).__name__}")

        # Accept empty parts -- they do not affect the join.
        if part == "":
            continue

        # Layer 1: reject absolute components.
        if posixpath.isabs(part):
            raise ValueError(f"part {idx} is an absolute path: {part!r}")
        if _WIN_DRIVE_RE.match(part):
            raise ValueError(f"part {idx} is an absolute Windows path: {part!r}")

        # Layer 2: reject any traversal component equal to '..'.
        # Split on '/' (posix separator) to inspect individual segments.
        for component in part.split("/"):
            if component == "..":
                raise ValueError(
                    f"part {idx} contains a traversal component '..': {part!r}"
                )

        clean_parts.append(part)

    # Layer 3: join, normalize, and verify containment.
    if clean_parts:
        joined = posixpath.join(norm_base, *clean_parts)
    else:
        joined = norm_base
    norm_result = posixpath.normpath(joined)

    if norm_result != norm_base and not norm_result.startswith(norm_base + "/"):
        raise ValueError(
            f"normalized result {norm_result!r} escapes base {norm_base!r}"
        )

    return norm_result
