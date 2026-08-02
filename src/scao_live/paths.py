"""Safe path joining utilities.

Provides :func:`safe_join` to join a base directory with path components while
guaranteeing the resolved result stays within the base directory. This is
useful when constructing filesystem paths from untrusted or partially trusted
input (for example: agent worktree boundaries, sandboxed scratch directories,
or user-supplied relative paths).

The safety guarantee is enforced with defence in depth:

1. Each ``part`` is rejected if it is absolute on the host platform.
2. Each ``part`` is rejected if any of its path components equals ``..``.
3. The fully resolved candidate (symlinks followed) must remain inside the
   resolved ``base``; otherwise the join is rejected even if the textual path
   looked innocent.

Step 3 is what catches symlink-based escapes that steps 1 and 2 cannot detect
on their own.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

__all__ = ["safe_join", "PathLike"]

PathLike = Union[str, "os.PathLike[str]"]


def safe_join(base: PathLike, *parts: PathLike) -> Path:
    """Join ``base`` with ``parts`` and return the resolved path.

    The returned :class:`pathlib.Path` is guaranteed to remain within ``base``
    after full resolution (symlinks included).

    Args:
        base: The anchor directory. Must exist on disk so it can be resolved
            unambiguously.
        *parts: Additional path components to join under ``base``. Each part
            must be relative and must not contain a ``..`` component.

    Returns:
        The resolved :class:`pathlib.Path` that lives inside ``base``.

    Raises:
        FileNotFoundError: If ``base`` does not exist.
        ValueError: If any part is absolute, contains a ``..`` component, or
            the resolved result escapes ``base`` (for example via a symlink).
    """
    base_resolved = Path(base).resolve(strict=True)

    for index, part in enumerate(parts):
        part_path = Path(part)
        if part_path.is_absolute():
            raise ValueError(
                f"absolute part not allowed at index {index}: {part!r}"
            )
        for component in part_path.parts:
            if component == "..":
                raise ValueError(
                    f"'..' traversal component not allowed at index {index}: "
                    f"{part!r}"
                )

    candidate = base_resolved.joinpath(*parts)
    candidate_resolved = candidate.resolve(strict=False)

    # Confirm the resolved candidate stays inside the resolved base.
    # relative_to raises ValueError when candidate_resolved is not under
    # base_resolved; we re-raise with a clearer message.
    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"resolved path {candidate_resolved!s} escapes base "
            f"{base_resolved!s}"
        ) from exc

    return candidate_resolved
