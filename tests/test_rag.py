"""
Tests for RAG module.
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.rag import RAGEngine, get_rag_engine
from backend.app.schema import Lab, Step, QA


class TestRAGEngine:
    """Tests for RAGEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a RAGEngine instance."""
        return RAGEngine()
    
    @pytest.fixture
    def sample_lab(self):
        """Create a sample lab for testing."""
        return Lab(
            lab_id="test-lab",
            title="Test Lab",
            chapter="1",
            objective="Learn testing",
            steps=[
                Step(id="1", desc="First step", cmds=["enable"], checklist=["Prompt shows #"]),
                Step(id="2", desc="Second step", cmds=["configure terminal"], checklist=[]),
                Step(id="3", desc="Configure hostname", cmds=["hostname R1"], checklist=["Prompt shows R1"])
            ],
            qa=[
                QA(q="What is enable?", a="Enters privileged EXEC mode"),
                QA(q="How to enter config mode?", a="Use configure terminal command")
            ]
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.labs == {}
        assert engine.documents == []
        assert engine.vectorstore is None
    
    def test_load_lab(self, engine, sample_lab):
        """Test loading a lab into the engine."""
        engine.load_lab(sample_lab)
        
        assert sample_lab.lab_id in engine.labs
        assert len(engine.documents) > 0
        
        # Should have documents for steps, Q&A, and objective
        doc_types = set(d["metadata"]["type"] for d in engine.documents)
        assert "step" in doc_types
        assert "qa" in doc_types
        assert "objective" in doc_types
    
    def test_load_from_json(self, engine, tmp_path):
        """Test loading a lab from JSON file."""
        lab_data = {
            "lab_id": "json-test",
            "title": "JSON Test Lab",
            "steps": [
                {"id": "1", "desc": "Test step", "cmds": ["test"], "checklist": []}
            ],
            "qa": []
        }
        
        json_path = tmp_path / "test_lab.json"
        with open(json_path, 'w') as f:
            json.dump(lab_data, f)
        
        lab = engine.load_from_json(str(json_path))
        
        assert lab.lab_id == "json-test"
        assert "json-test" in engine.labs
    
    def test_keyword_search(self, engine, sample_lab):
        """Test keyword-based search fallback."""
        engine.load_lab(sample_lab)
        
        # Search for something in the lab
        results = engine._keyword_search("enable", k=3)
        
        assert len(results) > 0
        assert any("enable" in r["content"].lower() for r in results)
    
    def test_search_with_no_results(self, engine, sample_lab):
        """Test search with no matching results."""
        engine.load_lab(sample_lab)
        
        results = engine._keyword_search("xyznonexistent", k=3)
        
        assert len(results) == 0
    
    def test_get_step_commands(self, engine, sample_lab):
        """Test getting commands for a step."""
        engine.load_lab(sample_lab)
        
        cmds = engine.get_step_commands("test-lab", "1")
        assert cmds == ["enable"]
        
        cmds = engine.get_step_commands("test-lab", "3")
        assert cmds == ["hostname R1"]
    
    def test_get_step_commands_nonexistent(self, engine, sample_lab):
        """Test getting commands for non-existent step."""
        engine.load_lab(sample_lab)
        
        cmds = engine.get_step_commands("test-lab", "99")
        assert cmds == []
        
        cmds = engine.get_step_commands("nonexistent", "1")
        assert cmds == []
    
    def test_get_step_hint(self, engine, sample_lab):
        """Test getting step hint."""
        engine.load_lab(sample_lab)
        
        hint = engine.get_step_hint("test-lab", "1")
        assert hint == "First step"
        
        hint = engine.get_step_hint("test-lab", "3")
        assert hint == "Configure hostname"
    
    def test_get_step_hint_nonexistent(self, engine, sample_lab):
        """Test getting hint for non-existent step."""
        engine.load_lab(sample_lab)
        
        hint = engine.get_step_hint("test-lab", "99")
        assert hint is None


class TestRAGAnswering:
    """Tests for RAG Q&A functionality."""
    
    @pytest.fixture
    def engine_with_lab(self):
        """Create engine with loaded lab."""
        engine = RAGEngine()
        lab = Lab(
            lab_id="qa-test",
            title="Q&A Test Lab",
            steps=[
                Step(id="1", desc="Enter enable mode", cmds=["enable"], checklist=[])
            ],
            qa=[
                QA(q="What is enable command?", a="The enable command enters privileged EXEC mode"),
                QA(q="How to configure hostname?", a="Use the hostname command in global config mode")
            ]
        )
        engine.load_lab(lab)
        return engine
    
    def test_answer_question_with_context(self, engine_with_lab):
        """Test answering question with lab context."""
        response = engine_with_lab.answer_question(
            "What is enable?",
            lab_id="qa-test"
        )
        
        assert response.response is not None
        assert len(response.response) > 0
    
    def test_answer_question_with_step_context(self, engine_with_lab):
        """Test answering with step context provides commands."""
        response = engine_with_lab.answer_question(
            "What should I do?",
            lab_id="qa-test",
            step_id="1"
        )
        
        assert response.suggested_commands == ["enable"]
        assert response.current_step_hint == "Enter enable mode"
    
    def test_answer_no_match(self, engine_with_lab):
        """Test answering when no match found."""
        response = engine_with_lab.answer_question(
            "completely unrelated random query xyz"
        )
        
        # Should still return a response
        assert response.response is not None


class TestGlobalRAGEngine:
    """Tests for global RAG engine."""
    
    def test_get_rag_engine(self):
        """Test getting global engine."""
        engine = get_rag_engine()
        assert engine is not None
        assert isinstance(engine, RAGEngine)
    
    def test_singleton_pattern(self):
        """Test that get_rag_engine returns same instance."""
        engine1 = get_rag_engine()
        engine2 = get_rag_engine()
        assert engine1 is engine2


class TestRAGWithFixture:
    """Tests using JSON fixture."""
    
    def test_load_sample_fixture(self):
        """Test loading sample lab fixture into RAG."""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "sample_lab.json"
        )
        
        engine = RAGEngine()
        lab = engine.load_from_json(fixture_path)
        
        assert lab.lab_id == "2.1.3"
        assert len(engine.documents) > 0
        
        # Test search
        results = engine.search("hostname", k=3)
        assert len(results) > 0
        
        # Test Q&A
        response = engine.answer_question(
            "What command enters privileged mode?",
            lab_id="2.1.3"
        )
        assert "enable" in response.response.lower() or len(response.response) > 0
