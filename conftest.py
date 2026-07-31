"""Pytest configuration: make the ``src``-layout package importable.

Adds the ``src`` directory to :data:`sys.path` so that test modules can
import :mod:`scao_live` without installing the package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
