"""Isolated replay: count items explicitly marked active in the input."""
import json
from pathlib import Path
import sys

items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(json.dumps({"count": sum(item["active"] is True for item in items)}, sort_keys=True))
