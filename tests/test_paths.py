"""Tests for :func:`scao_live.paths.safe_join`.

The tests cover basic joining behaviour and the security properties required
by the task plan:

* rejection of ``..`` traversal components,
* rejection of absolute components (POSIX and Windows drive style),
* rejection of nested traversal hidden inside longer components,
* handling of alternate path separators (``\\`` and ``/``) on every platform,
* rejection of symlink-style escape via a real filesystem fixture, and
* acceptance of legitimate sub-paths including ``sub/../file`` that stay
  inside the base.
"""

from __future__ import annotations

import os
import sys

import pytest

from scao_live.paths import SafeJoinError, safe_join


# ---------------------------------------------------------------------------
# Happy-path behaviour
# ---------------------------------------------------------------------------


def test_basic_join(tmp_path):
    """Joining several components yields the resolved absolute path."""
    result = safe_join(tmp_path, "sub", "file.txt")
    expected = os.path.realpath(str(tmp_path / "sub" / "file.txt"))
    assert result == expected


def test_single_component(tmp_path):
    result = safe_join(tmp_path, "file.txt")
    assert result == os.path.realpath(str(tmp_path / "file.txt"))


def test_no_components_returns_base(tmp_path):
    """With no components, the resolved base directory itself is returned."""
    assert safe_join(tmp_path) == os.path.realpath(str(tmp_path))


def test_accepts_string_base(tmp_path):
    result = safe_join(str(tmp_path), "file.txt")
    assert result == os.path.realpath(str(tmp_path / "file.txt"))


def test_accepts_pathlib_components(tmp_path):
    from pathlib import Path

    result = safe_join(tmp_path, Path("sub"), Path("file.txt"))
    assert result == os.path.realpath(str(tmp_path / "sub" / "file.txt"))


def test_subdir_dotdot_staying_inside_base(tmp_path):
    """``sub/../file`` is still inside the base and must be accepted."""
    result = safe_join(tmp_path, "sub", "..", "file.txt")
    assert result == os.path.realpath(str(tmp_path / "file.txt"))


def test_result_is_string(tmp_path):
    """The contract is that the return value is a ``str``."""
    assert isinstance(safe_join(tmp_path, "file.txt"), str)


# ---------------------------------------------------------------------------
# Rejection of ``..`` traversal
# ---------------------------------------------------------------------------


def test_rejects_dotdot_traversal(tmp_path):
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "..", "etc", "passwd")


def test_rejects_nested_dotdot_traversal(tmp_path):
    """A traversal hidden inside a longer component must be rejected."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "sub", "..", "..", "etc")


def test_rejects_dotdot_in_single_component(tmp_path):
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "../../etc/passwd")


def test_rejects_dotdot_exactly_to_parent(tmp_path):
    """``..`` alone resolves to the parent of the base and must be rejected."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "..")


# ---------------------------------------------------------------------------
# Rejection of absolute components
# ---------------------------------------------------------------------------


def test_rejects_absolute_posix_component(tmp_path):
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "/etc/passwd")


def test_rejects_absolute_windows_drive_component(tmp_path):
    """``C:\\Windows`` is absolute under Windows and must always be rejected.

    ``ntpath.isabs`` recognises drive letters regardless of host platform, so
    this test passes on POSIX as well.
    """
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "C:\\Windows\\System32")


def test_rejects_absolute_component_in_middle(tmp_path):
    """An absolute component anywhere in the chain must be rejected."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "sub", "/etc/passwd", "more")


# ---------------------------------------------------------------------------
# Alternate separators
# ---------------------------------------------------------------------------


def test_rejects_backslash_traversal(tmp_path):
    """Backslash-separated traversal is rejected on every platform."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, r"sub\..\..\etc")


def test_rejects_mixed_separator_traversal(tmp_path):
    """A component mixing ``/`` and ``\\`` to traverse must be rejected."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, r"sub/..\..\etc")


def test_rejects_backslash_drive_component(tmp_path):
    """Drive-style component with backslashes is rejected as absolute."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "C:\\evil")


# ---------------------------------------------------------------------------
# Symlink-style escape via a real filesystem fixture
# ---------------------------------------------------------------------------


def _can_symlink() -> bool:
    """Return ``True`` if the host can create a real symlink right now."""
    if not hasattr(os, "symlink"):
        return False
    import tempfile

    fd, name = tempfile.mkstemp()
    os.close(fd)
    try:
        target = name + "_link"
        try:
            os.symlink(name, target)
        except (OSError, NotImplementedError, ValueError):
            return False
        finally:
            if os.path.lexists(target):
                os.unlink(target)
    finally:
        os.unlink(name)
    return True


def test_rejects_symlink_escape(tmp_path):
    """A symlink inside the base pointing outside must be detected.

    The test is skipped when the host cannot create symlinks (e.g. unprivileged
    Windows without Developer Mode), so the suite remains portable.
    """
    if not _can_symlink():
        pytest.skip("symlinks are not supported in this environment")

    # Place the outside target as a sibling of ``tmp_path`` so that resolving
    # the link escapes the base directory.  A unique suffix avoids collisions
    # with concurrent pytest runs sharing the same temp root.
    outside = tmp_path.parent / f"outside_target_{os.getpid()}_{id(tmp_path):x}"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "evil_link"
    try:
        os.symlink(str(outside), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, ValueError) as exc:
        pytest.skip(f"symlink creation failed: {exc}")

    try:
        with pytest.raises(SafeJoinError):
            safe_join(tmp_path, "evil_link", "secret.txt")
    finally:
        if os.path.lexists(str(link)):
            os.unlink(str(link))
        if outside.exists():
            outside.rmdir()


def test_symlink_pointing_inside_base_is_allowed(tmp_path):
    """A symlink that stays inside the base must be accepted."""
    if not _can_symlink():
        pytest.skip("symlinks are not supported in this environment")

    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "file.txt").write_text("ok", encoding="utf-8")

    link = tmp_path / "good_link"
    try:
        os.symlink(str(real_dir), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, ValueError) as exc:
        pytest.skip(f"symlink creation failed: {exc}")

    try:
        result = safe_join(tmp_path, "good_link", "file.txt")
        assert result == os.path.realpath(str(real_dir / "file.txt"))
    finally:
        if os.path.lexists(str(link)):
            os.unlink(str(link))


# ---------------------------------------------------------------------------
# Type handling
# ---------------------------------------------------------------------------


def test_rejects_non_path_input(tmp_path):
    with pytest.raises(TypeError):
        safe_join(tmp_path, 42)


def test_rejects_non_path_base():
    with pytest.raises(TypeError):
        safe_join(42, "file.txt")


def test_bytes_component_decoded(tmp_path):
    """Bytes components are decoded as UTF-8 and accepted if safe."""
    result = safe_join(tmp_path, b"sub", b"file.txt")
    assert result == os.path.realpath(str(tmp_path / "sub" / "file.txt"))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_component_stays_in_base(tmp_path):
    """An empty component resolves back to the base and must be accepted."""
    result = safe_join(tmp_path, "")
    assert result == os.path.realpath(str(tmp_path))


def test_siblings_with_prefix_overlap_are_rejected(tmp_path):
    """A result that shares a prefix with the base but is a sibling is rejected.

    This guards against naive ``startswith``-based containment checks.
    """
    sibling = tmp_path.parent / (tmp_path.name + "_sibling")
    try:
        sibling.mkdir(exist_ok=True)
        # ``../<base>_sibling`` shares the parent prefix but is not inside base.
        with pytest.raises(SafeJoinError):
            safe_join(tmp_path, "..", sibling.name)
    finally:
        if sibling.exists():
            sibling.rmdir()


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="drive-specific containment only meaningful on Windows",
)
def test_different_drive_rejected_on_windows(tmp_path):
    """A component resolving to a different drive is rejected."""
    with pytest.raises(SafeJoinError):
        safe_join(tmp_path, "D:", "evil")
