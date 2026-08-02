"""Pytest root configuration.

Ensures the local ``src`` layout is importable ahead of any editable
install that may point at a different worktree.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
