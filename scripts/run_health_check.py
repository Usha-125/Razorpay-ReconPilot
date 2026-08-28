"""Simple health check runner that imports the health handler directly.

This avoids requiring FastAPI to be installed when merely validating the handler.
"""
import sys
import os

# Ensure repository root is on sys.path for imports when running scripts directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.health import get_health


def run():
    h = get_health()
    print("Health:", h)


if __name__ == "__main__":
    run()
