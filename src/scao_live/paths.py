from __future__ import annotations

from pathlib import Path

PathLike = str | Path


def safe_join(base: PathLike, *parts: PathLike) -> str:
    """Join ``base`` with ``parts`` without allowing path traversal escape.

    The base and the resulting candidate are resolved with :meth:`Path.resolve`
    so that ``..`` segments are normalized before any containment decision is
    made. Any part that is itself an absolute path is rejected up front, and a
    candidate that resolves outside the resolved base directory raises
    ``ValueError``.

    Args:
        base: The base directory that all parts must stay within.
        *parts: Path components to join underneath ``base``.

    Returns:
        The resolved candidate path as a string.

    Raises:
        ValueError: If any part is absolute, or if the joined candidate
            resolves outside the resolved base directory.
    """
    resolved_base = Path(base).resolve()

    string_parts: list[str] = []
    for part in parts:
        part_path = Path(part)
        if part_path.is_absolute():
            raise ValueError(f"absolute path part is not allowed: {part!r}")
        string_parts.append(str(part_path))

    candidate = resolved_base.joinpath(*string_parts)
    resolved_candidate = candidate.resolve()

    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(
            f"candidate path {candidate} escapes base {resolved_base}"
        ) from exc

    return str(resolved_candidate)
