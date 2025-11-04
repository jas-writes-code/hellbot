# i have no idea how this works

import os
import json
from pathlib import Path

BASE_PATH = Path(__file__).parent / "json"

class InfoNamespace:
    """Dynamic auto-expanding namespace (e.g., info.effects.planetEffects)."""
    def __init__(self):
        pass

    def __getattr__(self, key):
        if key not in self.__dict__:
            self.__dict__[key] = InfoNamespace()
        return self.__dict__[key]

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"<InfoNamespace {list(self.__dict__.keys())}>"

def load_json_files(base_path: Path) -> InfoNamespace:
    """Recursively load JSON files into nested InfoNamespace objects, skipping hidden ones."""
    namespace = InfoNamespace()

    for root, dirs, files in os.walk(base_path):
        # skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        files = [f for f in files if f.endswith(".json") and not f.startswith(".")]

        rel_path = Path(root).relative_to(base_path)
        current = namespace

        # traverse down to the correct sub-namespace
        for part in rel_path.parts:
            # only create a new namespace if it doesn't already exist or isn't one
            if not hasattr(current, part) or not isinstance(getattr(current, part), InfoNamespace):
                setattr(current, part, InfoNamespace())
            current = getattr(current, part)

        # load each JSON file into the current namespace
        for file in files:
            key = Path(file).stem
            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    setattr(current, key, data)
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to load {file_path}: {e}")

    return namespace

# Load everything at import time
info = load_json_files(BASE_PATH)
