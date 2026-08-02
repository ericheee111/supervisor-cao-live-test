"""Safe path joining utilities.

Provides :func:`safe_join` for joining untrusted path components onto a
trusted base directory while refusing to escape it.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["safe_join"]


def safe_join(base: str | os.PathLike[str], *parts: str | os.PathLike[str]) -> str:
    """Safely join *parts* onto *base*, refusing to escape the resolved base.

    The base directory is resolved to an absolute, canonical path. Each
    component in *parts* is then joined onto it and the result is resolved.
    The final path is only accepted when it remains inside *base*.

    Args:
        base: The trusted base directory. Resolved to an absolute path.
        *parts: Untrusted path components to join onto *base*.

    Returns:
        The resolved joined path as a string.

    Raises:
        ValueError: If any component is an absolute path, or if the joined
            result escapes the resolved base directory (for example via
            ``..`` traversal or a rooted component).
    """
    base_path = Path(base).resolve()

    for part in parts:
        if Path(part).is_absolute():
            raise ValueError(
                f"Absolute path component is not allowed: {os.fspath(part)!r}"
            )

    candidate = base_path.joinpath(*parts).resolve()

    if not candidate.is_relative_to(base_path):
        raise ValueError(
            f"Joined path {candidate!s} escapes base directory {base_path!s}"
        )

    return os.fspath(candidate)
