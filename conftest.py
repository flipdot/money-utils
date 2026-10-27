"""Pytest bootstrap for money-utils.

The application imports a machine-local ``config`` module that is not part of
the repository (developers copy ``config.example.py`` to ``config.py``).
For tests we load ``config.example.py`` instead, so the suite runs anywhere
without bank credentials, and we point ``db_path`` at a throwaway file so no
test can ever touch a real database.
"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import config  # noqa: F401  # developer's local config
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location("config", ROOT / "config.example.py")
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    sys.modules["config"] = config

# Even with a real config.py present, tests must never open the configured
# database file. Django's test runner uses an in-memory database, and the
# plain SQLAlchemy tests create their own in-memory engines; this only
# protects against accidental use.
config.db_path = os.path.join(tempfile.gettempdir(), "money-utils-tests.sqlite")
