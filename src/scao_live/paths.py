"""Path safety utilities for ``scao_live``.

This module provides :func:`safe_join`, the single funnel through which
untrusted path components are combined with a trusted base directory.
It rejects directory-traversal escapes and symlink-based breakouts so
that callers receive a resolved absolute path that is guaranteed to
remain within the base.
"""

from __future__ import annotations

import os
from pathlib import PurePath

__all__ = ["safe_join"]


def _contains_parent_segment(part: str) -> bool:
    """Return ``True`` if ``part`` contains a literal ``..`` segment.

    Splitting is performed with :class:`pathlib.PurePath`, which honours
    the native separator semantics of the running platform. On Windows
    both ``\\`` and ``/`` are separators; on POSIX only ``/`` is. A plain
    filename such as ``file..txt`` is *not* treated as traversal because
    ``..`` is not a standalone component of that path.
    """
    return ".." in PurePath(part).parts


def safe_join(base: str, *parts: str) -> str:
    """Safely join ``base`` with ``parts`` and return the resolved path.

    The join is performed with :func:`os.path.join` and both the base and
    the resulting candidate are resolved with :func:`os.path.realpath`
    so that symbolic links are followed and a real absolute path is
    produced.

    A :class:`ValueError` is raised whenever:

    * any supplied component in ``parts`` contains a ``..`` path
      segment, or
    * the resolved candidate falls outside the resolved base directory
      (this also rejects absolute components that override the base and
      symlink components that point outside the base).

    When ``parts`` is empty or every component is an empty string, the
    resolved base directory is returned unchanged, preserving the
    empty-join behaviour of :func:`os.path.join`.

    :param base: Trusted base directory. May be relative or absolute;
        it is resolved with :func:`os.path.realpath`.
    :param parts: Untrusted path components to join onto ``base``.
    :returns: The resolved absolute path of the candidate.
    :raises TypeError: if ``base`` or any component is not a string.
    :raises ValueError: if a component contains ``..`` or the resolved
        candidate escapes the resolved base.
    """
    if not isinstance(base, str):
        raise TypeError(f"base must be str, not {type(base).__name__}")

    for part in parts:
        if not isinstance(part, str):
            raise TypeError(
                f"path component must be str, not {type(part).__name__}"
            )
        if _contains_parent_segment(part):
            raise ValueError(
                f"path component contains a traversal segment: {part!r}"
            )

    base_resolved = os.path.realpath(base)
    candidate = os.path.join(base, *parts)
    candidate_resolved = os.path.realpath(candidate)

    # Compare case-insensitively on case-insensitive filesystems
    # (Windows) and case-sensitively elsewhere. A trailing separator on
    # the base (e.g. a drive root such as "C:\") is preserved so the
    # prefix check does not double the separator.
    base_nc = os.path.normcase(base_resolved)
    cand_nc = os.path.normcase(candidate_resolved)
    sep = os.sep
    prefix = base_nc if base_nc.endswith(sep) else base_nc + sep

    if cand_nc != base_nc and not cand_nc.startswith(prefix):
        raise ValueError(
            f"resolved path {candidate_resolved!r} escapes base "
            f"{base_resolved!r}"
        )

    return candidate_resolved
