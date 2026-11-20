"""Read-only pitch examples, separate from enrolled vendors and customer feedback."""
import json
from pathlib import Path

def kgp_venues():
    return json.loads(Path(__file__).with_name('demo_kgp.json').read_text())
