"""Path joining utilities with safety checks.

Provides :func:`safe_join` to compose filesystem paths from a trusted base
and untrusted string parts while rejecting absolute components and ``..``
path segments that could escape the base directory.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ["safe_join", "PathSafetyError"]

# Matches a Windows drive specifier at the start of a path component, e.g.
# ``C:\\`` or ``D:/``. Used to reject Windows-absolute parts on any platform.
_DRIVE_RE: Final = re.compile(r"^[A-Za-z]:[\\/]")


class PathSafetyError(ValueError):
    """Raised when a path part violates the safety constraints of safe_join."""


def _is_absolute_part(part: str) -> bool:
    """Return ``True`` if ``part`` is an absolute path on any platform.

    Recognizes Unix absolute paths (leading ``/``), Windows UNC paths
    (leading ``\\``), and Windows drive-absolute paths (``C:\\`` or
    ``C:/``).
    """
    if not part:
        return False
    if part[0] in ("/", "\\"):
        return True
    return bool(_DRIVE_RE.match(part))


def _validate_part(part: str) -> None:
    """Validate that ``part`` is safe to join under the trusted base.

    Rejects absolute paths and any component containing a ``..`` segment,
    including embedded segments such as ``a/../b``.
    """
    if _is_absolute_part(part):
        raise PathSafetyError(
            "absolute path components are not allowed: " + repr(part)
        )
    for segment in part.replace("\\", "/").split("/"):
        if segment == "..":
            raise PathSafetyError(
                "'..' path segments are not allowed in " + repr(part)
            )


def safe_join(base: str, *parts: str) -> str:
    """Join ``base`` with ``parts`` using POSIX path separators.

    Safety rules enforced:

    - ``base`` and every part must be strings.
    - No part may be an absolute path (Unix ``/``, Windows drive ``C:\\``,
      Windows drive with forward slash ``C:/``, or UNC ``\\\\server``).
    - No part may contain a ``..`` segment anywhere, including embedded
      segments such as ``a/../b`` or trailing segments such as ``a/..``.
    - The trusted ``base`` is not semantically normalized; ``..`` and ``.``
      segments in the base are preserved as-is. Only path separators are
      normalized to POSIX ``/``.

    Args:
        base: The trusted base path.
        *parts: Untrusted path components to join under ``base``.

    Returns:
        The joined path as a POSIX-separated string.

    Raises:
        PathSafetyError: If ``base`` or any part is not a string, if any
            part is an absolute path, or if any part contains a ``..``
            segment.
    """
    if not isinstance(base, str):
        raise PathSafetyError(
            "base must be a string, got " + type(base).__name__
        )

    # Normalize the trusted base to POSIX separators without resolving its
    # semantic content (no ``..`` or ``.`` resolution).
    path = base.replace("\\", "/")

    for part in parts:
        if not isinstance(part, str):
            raise PathSafetyError(
                "part must be a string, got " + type(part).__name__
            )
        _validate_part(part)
        posix_part = part.replace("\\", "/")
        # Skip empty parts to avoid doubled separators, matching the
        # behavior of os.path.join for empty string components.
        if not posix_part:
            continue
        # Defensive: validation already rejected absolute parts, so this
        # branch should never trigger. Kept as a safety net.
        if posix_part.startswith("/"):
            path = posix_part
        elif not path or path.endswith("/"):
            path += posix_part
        else:
            path += "/" + posix_part
    return path
