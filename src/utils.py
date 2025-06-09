# utils.py
"""
Funzioni di utilità, come il logger di debug.
"""
import sys
from .config import DEBUG

def dbg(msg: str):
    """Stampa un messaggio di debug su stderr se DEBUG è True."""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)