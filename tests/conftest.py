"""Pytest configuration helpers."""
import os
import sys
from pathlib import Path

# Ensure email validation does not perform DNS lookups during tests.
os.environ["EMAIL_CHECK_DELIVERABILITY"] = "false"

# Ensure the project root is available on sys.path so that `import src` works.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
