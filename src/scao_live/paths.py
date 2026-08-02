"""Path safety utilities for the Supervisor-CAO live runtime.

This module provides :func:`safe_join`, a containment-checked replacement for
:func:`os.path.join` that prevents path-traversal attacks.  It rejects inputs
that would escape the base directory via:

* absolute components (POSIX ``/`` or Windows drive ``C:\\`` style),
* ``..`` traversal components,
* nested traversal hidden inside longer components,
* alternate path separators (``\\`` on POSIX, ``/`` on Windows), and
* symlink resolution that points outside the base directory.

The function never trusts :func:`os.path.join` on its own: every result is
re-resolved with :func:`os.path.realpath` and verified to remain inside the
resolved base directory before being returned.
"""

from __future__ import annotations

import ntpath
import os
import posixpath
from typing import Union

PathLike = Union[str, bytes, "os.PathLike[str]"]

__all__ = ["SafeJoinError", "safe_join"]


class SafeJoinError(ValueError):
    """Raised when a path component would escape the base directory."""


def _is_absolute_anywhere(component: str) -> bool:
    """Return ``True`` if *component* is absolute under either POSIX or Windows.

    A component such as ``C:\\Windows`` is absolute under Windows even when the
    host operating system is POSIX; catching it here prevents
    :func:`os.path.join` from silently discarding the base on either platform.
    """
    return posixpath.isabs(component) or ntpath.isabs(component)


def _normalize_separators(component: str) -> str:
    """Normalize both ``/`` and ``\\`` to :data:`os.sep`.

    On Windows both characters are path separators; on POSIX only ``/`` is.
    Treating both as separators everywhere means a traversal such as
    ``sub\\..\\..\\etc`` cannot slip past the containment check simply because
    the joiner does not recognise one of the separators.
    """
    # Replace backslash first, then forward slash, so the final string only
    # uses the host separator.  Drive letters (e.g. ``C:``) are left intact.
    return component.replace("\\", "/").replace("/", os.sep)


def _to_str(component: PathLike) -> str:
    """Coerce a path-like component to ``str`` with strict UTF-8 decoding."""
    if not isinstance(component, (str, bytes, os.PathLike)):
        raise TypeError(
            f"Component must be str, bytes, or os.PathLike, got "
            f"{type(component).__name__}"
        )
    raw = os.fspath(component)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="strict")
    return raw


def safe_join(base: PathLike, *components: PathLike) -> str:
    """Join *components* onto *base* and verify the result stays inside *base*.

    Behaviour:

    * With no components, the resolved absolute path of *base* itself is
      returned.
    * Any absolute component (POSIX or Windows style) raises
      :class:`SafeJoinError`, because :func:`os.path.join` would otherwise
      discard *base*.
    * Alternate path separators are normalized before joining, so a component
      such as ``sub\\..\\..\\etc`` is treated as traversal on every platform.
    * The joined path is resolved with :func:`os.path.realpath`, which also
      resolves symlinks, and the resolved path must remain inside the resolved
      base directory.  If it does not, :class:`SafeJoinError` is raised.
    * The returned value is the resolved absolute path as a ``str``.

    Args:
        base: The base directory that every result must remain inside.
        *components: Path components to join onto *base*.

    Returns:
        The resolved absolute path of the joined location, as ``str``.

    Raises:
        SafeJoinError: If any component would cause the result to escape
            *base*.
        TypeError: If a component is not path-like.

    Examples:
        >>> import os
        >>> safe_join("/tmp/base", "sub", "file.txt") == os.path.realpath(
        ...     "/tmp/base/sub/file.txt"
        ... )
        True
        >>> safe_join("/tmp/base", "../etc/passwd")
        Traceback (most recent call last):
            ...
        scao_live.paths.SafeJoinError: ...
    """
    base_str = _to_str(base)

    if not components:
        # Nothing to join: resolve and return the base itself.  The base is
        # always "inside" itself, so no containment check is required.
        return os.path.realpath(base_str)

    component_strs: list[str] = []
    for comp in components:
        c = _to_str(comp)
        if _is_absolute_anywhere(c):
            raise SafeJoinError(
                f"Absolute path component is not allowed: {c!r}"
            )
        component_strs.append(_normalize_separators(c))

    joined = os.path.join(base_str, *component_strs)

    base_real = os.path.realpath(base_str)
    target_real = os.path.realpath(joined)

    try:
        common = os.path.commonpath([base_real, target_real])
    except ValueError:
        # Raised by ``commonpath`` when the paths live on different drives
        # (Windows) or are otherwise incomparable.  That always means the
        # target is not inside the base.
        raise SafeJoinError(
            f"Path escapes base directory: target {target_real!r} is not "
            f"comparable to base {base_real!r}"
        ) from None

    if common != base_real:
        raise SafeJoinError(
            f"Path escapes base directory: {joined!r} resolves to "
            f"{target_real!r} which is outside {base_real!r}"
        )

    return target_real
