"""Safe path joining utilities.

Provides :func:`safe_join` for concatenating an untrusted sequence of path
components onto a trusted base without allowing directory traversal or
absolute-path escapes.
"""

from __future__ import annotations

import re

__all__ = ["safe_join"]

_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def _require_string(value: object, name: str) -> None:
    """Raise ``TypeError`` if *value* is not a ``str``."""
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string, got {type(value).__name__}"
        )


def _is_absolute_component(part: str) -> bool:
    """Return ``True`` if *part* looks like an absolute path on any platform.

    Covers POSIX leading ``/``, Windows leading ``\\``, and Windows drive
    letters such as ``C:``.
    """
    if part.startswith(("/", "\\")):
        return True
    return bool(_DRIVE_RE.match(part))


def _contains_traversal(part: str) -> bool:
    """Return ``True`` if *part* contains a ``..`` path segment.

    Both POSIX (``/``) and Windows (``\\``) separators are considered so
    that traversal cannot sneak in via a Windows-style component.
    """
    normalized = part.replace("\\", "/")
    return ".." in normalized.split("/")


def safe_join(base: str, *parts: str) -> str:
    """Join *base* and *parts* into a POSIX-separated path string.

    The *base* is treated as trusted and is returned verbatim - it is not
    normalized and ``..`` segments inside it are preserved.  Each entry in
    *parts* is treated as untrusted and is validated:

    * It must be a ``str`` (otherwise ``TypeError``).
    * It must not be an absolute path - i.e. it must not start with ``/``,
      ``\\``, or a Windows drive letter such as ``C:`` (otherwise
      ``ValueError``).
    * It must not contain any ``..`` path segment when split on ``/`` or
      ``\\`` (otherwise ``ValueError``).

    Components are joined with the POSIX separator (``/``).  No filesystem
    access is performed and the base is never normalized.
    """
    _require_string(base, "base")

    segments: list[str] = [base]

    for index, part in enumerate(parts):
        param_name = f"parts[{index}]"
        _require_string(part, param_name)

        if _is_absolute_component(part):
            raise ValueError(
                f"{param_name} must not be an absolute path: {part!r}"
            )
        if _contains_traversal(part):
            raise ValueError(
                f"{param_name} must not contain '..' segments: {part!r}"
            )

        segments.append(part)

    return "/".join(segments)
