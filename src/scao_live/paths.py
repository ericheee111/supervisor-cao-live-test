from __future__ import annotations

from pathlib import Path

__all__ = ["safe_join"]


def safe_join(base: str | Path, *parts: str | Path) -> str:
    """Safely join *parts* onto *base*, refusing to escape the base directory.

    Absolute parts are rejected up front. The *base* and the joined candidate
    are resolved with :meth:`pathlib.Path.resolve`, and containment is enforced
    via :meth:`pathlib.Path.relative_to`. Any part sequence that would escape
    the resolved base raises :class:`ValueError`.

    Args:
        base: The containing directory. Resolved to an absolute path.
        *parts: Path components to join onto *base*. Must be relative.

    Returns:
        The resolved candidate path as a string, guaranteed to be at or
        beneath the resolved *base*.

    Raises:
        ValueError: If any part is absolute, or if the joined result escapes
            the resolved base directory.
    """
    resolved_base = Path(base).resolve()

    for part in parts:
        if Path(part).is_absolute():
            raise ValueError(f"Absolute path part is not allowed: {part!r}")

    candidate = resolved_base.joinpath(*parts).resolve()
    candidate.relative_to(resolved_base)

    return str(candidate)
