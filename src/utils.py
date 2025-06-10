# utils.py
"""
Utility functions for debugging and logging.
"""
import sys
from .config import DEBUG

def dbg(msg: str):
    """Prints a debug message to stderr if DEBUG is True."""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)