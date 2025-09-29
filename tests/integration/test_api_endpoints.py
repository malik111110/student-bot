"""
Integration tests for API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


class TestAPIEndpoints:
    """Test API endpoint functionality."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root health check endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation endpoint."""
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "Promo Section Bot"

    @patch("core.data_loader.load_json_data")
    def test_courses_endpoint(self, mock_load_data, client):
        """Test courses API endpoint."""
        # Mock course data
        mock_load_data.return_value = [
            {
                "code": "INFOSEC_CRYPTO",
                "name": "Cryptography",
                "field": "INFOSEC",
                "credits": 5,
            }
        ]

        response = client.get("/api/v1/courses")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "INFOSEC_CRYPTO"

    @patch("core.data_loader.load_json_data")
    def test_professors_endpoint(self, mock_load_data, client):
        """Test professors API endpoint."""
        # Mock professor data
        mock_load_data.return_value = [
            {
                "name": "MAKHLOUF",
                "email": "sidahmed.makhlouf@gmail.com",
                "courses": ["Piratage éthique"],
            }
        ]

        response = client.get("/api/v1/professors")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "MAKHLOUF"

    @patch("core.data_loader.load_json_data")
    def test_schedule_endpoint(self, mock_load_data, client):
        """Test schedule API endpoint."""
        # Mock schedule data
        mock_load_data.return_value = {
            "securite_informatique": {
                "sunday": [
                    {
                        "time": "08:30-10:00",
                        "course": "Cours AAC",
                        "professor": "LEBBAH",
                        "room": "Salle B1",
                    }
                ]
            }
        }

        response = client.get("/api/v1/schedule")

        assert response.status_code == 200
        data = response.json()
        assert "securite_informatique" in data

    def test_schedule_by_field_endpoint(self, client):
        """Test schedule by field endpoint."""
        with patch("core.data_loader.load_json_data") as mock_load:
            mock_load.return_value = {
                "securite_informatique": {
                    "sunday": [{"time": "08:30-10:00", "course": "Test"}]
                }
            }

            response = client.get("/api/v1/schedule/securite_informatique")

            assert response.status_code == 200

    def test_schedule_invalid_field(self, client):
        """Test schedule endpoint with invalid field."""
        response = client.get("/api/v1/schedule/invalid_field")

        assert response.status_code == 404

    @patch("core.llm.get_llm_response")
    def test_ai_chat_endpoint(self, mock_llm, client):
        """Test AI chat endpoint."""
        mock_llm.return_value = "Test AI response"

        response = client.post(
            "/api/v1/ai/chat", json={"message": "Hello", "user_id": "test_user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @patch("core.news_scraper.scrape_news")
    def test_news_endpoint(self, mock_scraper, client):
        """Test news scraping endpoint."""
        mock_scraper.return_value = [
            {
                "title": "Test News",
                "url": "https://example.com",
                "summary": "Test summary",
            }
        ]

        response = client.get("/api/v1/news?source=hackernews")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test News"
