"""Isolated replay: count every item in the supplied synthetic input."""
import json
from pathlib import Path
import sys

items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(json.dumps({"count": len(items)}, sort_keys=True))
