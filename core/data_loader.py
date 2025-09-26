import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json_data(filename: str) -> list | dict:
    """Loads and returns data from a JSON file in the data directory."""
    try:
        with open(DATA_DIR / filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # In a real app, you might want to log this error
        return {}
    except json.JSONDecodeError:
        # And also log this
        return {}
