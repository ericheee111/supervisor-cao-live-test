"""Safe path joining utilities with containment enforcement.

Provides :func:`safe_join` to join a base directory with path components while
guaranteeing the resolved result stays within the base directory. This is
useful when constructing filesystem paths from untrusted or partially trusted
input (agent worktree boundaries, sandboxed scratch directories, user-supplied
relative paths, etc.).

Safety is enforced with defence in depth:

1. Each ``part`` is rejected if it is absolute on the host platform, including
   POSIX ``/``-rooted paths, Windows drive-letter paths (``C:\\...``), and
   Windows root-relative backslash paths (``\\...``) that ``is_absolute()``
   misses but ``joinpath`` treats as drive-rooted.
2. Each ``part`` is rejected if any of its path components equals ``..``.
3. The fully resolved candidate (symlinks followed) must remain inside the
   resolved ``base``; otherwise the join is rejected even if the textual path
   looked innocent. This is what catches symlink-based escapes that steps 1
   and 2 cannot detect on their own.
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
        FileNotFoundError: If ``base`` does not exist and therefore cannot be
            resolved unambiguously.
        ValueError: If any part is absolute, root-relative on Windows, contains
            a ``..`` component, or the resolved result escapes ``base`` (for
            example via a symlink).
    """
    base_resolved = Path(base).resolve(strict=True)

    for index, part in enumerate(parts):
        part_path = Path(part)

        # 1a. Reject absolute parts.
        # On POSIX this catches /etc.  On Windows this catches C:\Windows
        # (drive-letter absolute) but NOT \Windows (root-relative without a
        # drive), which is handled by the check below.
        if part_path.is_absolute():
            raise ValueError(
                f"absolute part not allowed at index {index}: {part!r}"
            )

        # 1b. On Windows, reject root-relative parts such as \Windows or
        # /etc that ``is_absolute()`` reports as non-absolute but that
        # ``Path.joinpath`` treats as anchoring to the current drive root,
        # discarding the base directory.
        if os.name == "nt":
            part_str = os.fspath(part)
            if part_str[:1] in ("\\", "/"):
                raise ValueError(
                    f"root-relative part not allowed at index {index}: "
                    f"{part!r}"
                )

        # 2. Reject any '..' traversal component, whether it is a standalone
        # part or embedded inside a multi-component part string.
        for component in part_path.parts:
            if component == "..":
                raise ValueError(
                    f"'..' traversal component not allowed at index {index}: "
                    f"{part!r}"
                )

    # 3. Build the candidate and fully resolve it (symlinks followed).
    candidate = base_resolved.joinpath(*parts)
    candidate_resolved = candidate.resolve(strict=False)

    # Confirm the resolved candidate stays inside the resolved base.
    # ``relative_to`` raises ValueError when ``candidate_resolved`` is not
    # under ``base_resolved``; we re-raise with a clearer message.
    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"resolved path {candidate_resolved!s} escapes base "
            f"{base_resolved!s}"
        ) from exc

    return candidate_resolved
