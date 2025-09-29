"""
Tests for data loader module.
"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from core.data_loader import load_json_data


class TestDataLoader:
    """Test data loading functionality."""

    def test_data_dir_exists(self):
        """Test that data directory path is correctly set."""
        from core.data_loader import DATA_DIR

        assert "data" in str(DATA_DIR)
        assert DATA_DIR.name == "data"

    @patch("builtins.open", new_callable=mock_open, read_data='{"test": "data"}')
    def test_load_json_data_success(self, mock_file):
        """Test successful JSON data loading."""
        result = load_json_data("test.json")

        assert result == {"test": "data"}
        mock_file.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_json_data_file_not_found(self, mock_file):
        """Test JSON loading with missing file."""
        result = load_json_data("missing.json")

        assert result == {}

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_load_json_data_invalid_json(self, mock_file):
        """Test JSON loading with invalid JSON."""
        result = load_json_data("invalid.json")

        assert result == {}

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"students": [{"name": "John"}]}',
    )
    def test_load_json_data_complex_structure(self, mock_file):
        """Test JSON loading with complex data structure."""
        result = load_json_data("students.json")

        assert result == {"students": [{"name": "John"}]}

    @patch("builtins.open", new_callable=mock_open, read_data='{"other": "data"}')
    def test_load_json_data_simple_structure(self, mock_file):
        """Test JSON loading with simple data structure."""
        result = load_json_data("test.json")

        assert result == {"other": "data"}

    def test_load_json_data_file_not_found_returns_empty_dict(self):
        """Test JSON loading returns empty dict for missing files."""
        result = load_json_data("nonexistent.json")

        assert result == {}
