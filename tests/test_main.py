"""
Tests for FastAPI main application.
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from backend.app.main import app, labs_storage, progress_storage
from backend.app.schema import Lab, Step, QA


@pytest.fixture
def client():
    """Create a test client."""
    # Clear storage before each test
    labs_storage.clear()
    progress_storage.clear()
    return TestClient(app)


@pytest.fixture
def sample_lab_data():
    """Sample lab data for testing."""
    return {
        "lab_id": "test-2.1.3",
        "title": "Test Router Configuration",
        "chapter": "2",
        "objective": "Learn router basics",
        "steps": [
            {"id": "1", "desc": "Enable", "cmds": ["enable"], "checklist": ["Prompt #"]},
            {"id": "2", "desc": "Config", "cmds": ["configure terminal"], "checklist": []}
        ],
        "qa": [
            {"q": "What is enable?", "a": "Enters privileged mode"}
        ]
    }


class TestRootEndpoints:
    """Tests for root endpoints."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestLabEndpoints:
    """Tests for lab management endpoints."""
    
    def test_load_lab_json(self, client, sample_lab_data):
        """Test loading lab from JSON."""
        response = client.post("/labs/json", json=sample_lab_data)
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == "test-2.1.3"
        assert len(data["steps"]) == 2
    
    def test_list_labs_empty(self, client):
        """Test listing labs when empty."""
        response = client.get("/labs")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_labs_with_data(self, client, sample_lab_data):
        """Test listing labs with data."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs")
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_get_lab(self, client, sample_lab_data):
        """Test getting specific lab."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3")
        assert response.status_code == 200
        assert response.json()["lab_id"] == "test-2.1.3"
    
    def test_get_lab_not_found(self, client):
        """Test getting non-existent lab."""
        response = client.get("/labs/nonexistent")
        assert response.status_code == 404
    
    def test_get_lab_json(self, client, sample_lab_data):
        """Test getting lab as JSON."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3/json")
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == "test-2.1.3"
    
    def test_delete_lab(self, client, sample_lab_data):
        """Test deleting a lab."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.delete("/labs/test-2.1.3")
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get("/labs/test-2.1.3")
        assert response.status_code == 404
    
    def test_delete_lab_not_found(self, client):
        """Test deleting non-existent lab."""
        response = client.delete("/labs/nonexistent")
        assert response.status_code == 404


class TestProgressEndpoints:
    """Tests for progress tracking endpoints."""
    
    def test_get_progress_initial(self, client, sample_lab_data):
        """Test getting initial progress."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == "test-2.1.3"
        assert data["current_step"] == 0
        assert data["completed_steps"] == []
        assert data["total_steps"] == 2
    
    def test_advance_step(self, client, sample_lab_data):
        """Test advancing to next step."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.post("/labs/test-2.1.3/progress/next")
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 1
        assert "1" in data["completed_steps"]
    
    def test_complete_specific_step(self, client, sample_lab_data):
        """Test completing a specific step."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.post("/labs/test-2.1.3/progress/complete/2")
        assert response.status_code == 200
        data = response.json()
        assert "2" in data["completed_steps"]
    
    def test_reset_progress(self, client, sample_lab_data):
        """Test resetting progress."""
        client.post("/labs/json", json=sample_lab_data)
        client.post("/labs/test-2.1.3/progress/next")
        
        response = client.post("/labs/test-2.1.3/progress/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 0
        assert data["completed_steps"] == []


class TestChatEndpoints:
    """Tests for chat endpoints."""
    
    def test_chat_basic(self, client, sample_lab_data):
        """Test basic chat."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.post("/chat", json={
            "message": "What is enable?",
            "lab_id": "test-2.1.3"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_with_step_context(self, client, sample_lab_data):
        """Test chat with step context."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.post("/chat", json={
            "message": "What should I do?",
            "lab_id": "test-2.1.3",
            "step_id": "1"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["suggested_commands"] == ["enable"]
    
    def test_search(self, client, sample_lab_data):
        """Test search endpoint."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/search?query=enable")
        assert response.status_code == 200
        assert "results" in response.json()


class TestCLIEndpoints:
    """Tests for CLI-related endpoints."""
    
    def test_compare_command(self, client):
        """Test command comparison."""
        response = client.post("/cli/compare?expected=enable&actual=enable")
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"]
    
    def test_compare_command_with_error(self, client):
        """Test command comparison with error."""
        response = client.post("/cli/compare?expected=hostname%20R1&actual=hostnam%20R1")
        assert response.status_code == 200
        data = response.json()
        # The comparison detects errors
        assert len(data["errors"]) > 0


class TestHintEndpoints:
    """Tests for hint endpoints."""
    
    def test_get_step_hint(self, client, sample_lab_data):
        """Test getting step hint."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3/steps/1/hint")
        assert response.status_code == 200
        data = response.json()
        assert data["step_id"] == "1"
        assert data["description"] == "Enable"
        assert data["commands"] == ["enable"]
    
    def test_get_step_hint_not_found(self, client, sample_lab_data):
        """Test getting hint for non-existent step."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3/steps/99/hint")
        assert response.status_code == 404
    
    def test_get_current_hint(self, client, sample_lab_data):
        """Test getting current hint based on progress."""
        client.post("/labs/json", json=sample_lab_data)
        response = client.get("/labs/test-2.1.3/current-hint")
        assert response.status_code == 200
        data = response.json()
        assert data["step_id"] == "1"
        assert "progress" in data
    
    def test_get_current_hint_completed(self, client, sample_lab_data):
        """Test current hint when lab is completed."""
        client.post("/labs/json", json=sample_lab_data)
        # Advance through all steps
        client.post("/labs/test-2.1.3/progress/next")
        client.post("/labs/test-2.1.3/progress/next")
        
        response = client.get("/labs/test-2.1.3/current-hint")
        assert response.status_code == 200
        data = response.json()
        assert "completed" in data["message"].lower()
