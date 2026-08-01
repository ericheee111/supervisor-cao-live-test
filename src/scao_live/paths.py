"""Path utilities with traversal protection."""

import os


def safe_join(base, *parts):
    """Join ``base`` with ``*parts`` using :func:`os.path.join`.

    Every supplied path part (including ``base``) is inspected for the
    ``'..'`` substring *before* :func:`os.path.join` is called. If any part
    contains ``'..'``, a :class:`ValueError` is raised to prevent directory
    traversal.

    Parameters
    ----------
    base : str
        The base path.
    *parts : str
        Additional path components to join onto ``base``.

    Returns
    -------
    str
        The joined path.

    Raises
    ------
    ValueError
        If any supplied path part contains ``'..'``.
    """
    for part in (base, *parts):
        if '..' in part:
            raise ValueError("path part contains '..': %r" % (part,))
    return os.path.join(base, *parts)
