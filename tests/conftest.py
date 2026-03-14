"""Shared test configuration — load hyphenated source modules for testing.

Both fetch-extras.py and rename-library.py use hyphens in their filenames,
so they can't be imported normally.  This conftest pre-loads them into
sys.modules so test files can simply ``from fetch_extras import ...``.

Note: loading fetch-extras.py executes its top-level code, which creates a
requests.Session.  No HTTP calls are made — the session is just an object
in memory.  We accept this rather than mocking, since the test command
(``uv run --with puzpy --with requests --with pytest pytest``) always has
both dependencies available.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_module(name, filename):
    """Load a Python file as a module and cache it in sys.modules."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Pre-load so test files can ``import fetch_extras`` / ``import rename_library``
_load_module("fetch_extras", "fetch-extras.py")
_load_module("rename_library", "rename-library.py")
