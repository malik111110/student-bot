import pytest
from core.data_loader import load_json_data, DATA_DIR

# Create dummy files for testing
@pytest.fixture(scope="module", autouse=True)
def create_dummy_data_files():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir()
    
    with open(DATA_DIR / "test.json", "w") as f:
        f.write('[{"id": 1, "value": "test"}]')
    with open(DATA_DIR / "invalid.json", "w") as f:
        f.write('this is not json')
        
    yield
    
    (DATA_DIR / "test.json").unlink()
    (DATA_DIR / "invalid.json").unlink()

def test_load_json_data_success():
    """Tests successful loading of a valid JSON file."""
    data = load_json_data("test.json")
    assert data == [{"id": 1, "value": "test"}]

def test_load_json_data_not_found():
    """Tests handling of a non-existent file."""
    data = load_json_data("nonexistent.json")
    assert data == {}

def test_load_json_data_decode_error():
    """Tests handling of an invalid JSON file."""
    data = load_json_data("invalid.json")
    assert data == {}
