"""Pytest configuration shared across tests."""
import sys
from pathlib import Path

# Make src/ importable without `pip install -e .` so CI on fresh checkout works.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
