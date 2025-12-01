"""
Tests for schema module.
"""

import pytest
from backend.app.schema import (
    Lab, Step, QA, StepProgress, CommandMatch,
    ChatRequest, ChatResponse
)


class TestStep:
    """Tests for Step model."""
    
    def test_step_creation(self):
        """Test basic step creation."""
        step = Step(
            id="1",
            desc="Configure hostname",
            cmds=["hostname R1"],
            checklist=["Prompt shows R1"]
        )
        assert step.id == "1"
        assert step.desc == "Configure hostname"
        assert step.cmds == ["hostname R1"]
        assert step.checklist == ["Prompt shows R1"]
    
    def test_step_empty_defaults(self):
        """Test step with empty defaults."""
        step = Step(id="1", desc="Test step")
        assert step.cmds == []
        assert step.checklist == []
    
    def test_step_multiple_commands(self):
        """Test step with multiple commands."""
        step = Step(
            id="5",
            desc="Configure console",
            cmds=["line console 0", "password cisco", "login", "exit"],
            checklist=[]
        )
        assert len(step.cmds) == 4


class TestLab:
    """Tests for Lab model."""
    
    def test_lab_creation(self):
        """Test basic lab creation."""
        lab = Lab(
            lab_id="2.1.3",
            title="Basic Router Configuration",
            chapter="2",
            objective="Learn router basics",
            steps=[
                Step(id="1", desc="Step 1", cmds=["enable"]),
                Step(id="2", desc="Step 2", cmds=["configure terminal"])
            ],
            qa=[
                QA(q="What is enable?", a="Enters privileged mode")
            ]
        )
        assert lab.lab_id == "2.1.3"
        assert lab.title == "Basic Router Configuration"
        assert len(lab.steps) == 2
        assert len(lab.qa) == 1
    
    def test_lab_minimal(self):
        """Test minimal lab creation."""
        lab = Lab(lab_id="1.0", title="Test Lab")
        assert lab.lab_id == "1.0"
        assert lab.steps == []
        assert lab.qa == []
        assert lab.chapter is None
        assert lab.objective is None
    
    def test_lab_json_serialization(self):
        """Test lab JSON serialization."""
        lab = Lab(
            lab_id="test",
            title="Test Lab",
            steps=[Step(id="1", desc="Step 1")]
        )
        json_str = lab.model_dump_json()
        assert "test" in json_str
        assert "Test Lab" in json_str


class TestQA:
    """Tests for QA model."""
    
    def test_qa_creation(self):
        """Test QA creation."""
        qa = QA(q="What is OSPF?", a="Open Shortest Path First routing protocol")
        assert qa.q == "What is OSPF?"
        assert "Shortest Path First" in qa.a


class TestStepProgress:
    """Tests for StepProgress model."""
    
    def test_progress_creation(self):
        """Test progress creation."""
        progress = StepProgress(
            lab_id="2.1.3",
            current_step=2,
            completed_steps=["1", "2"],
            total_steps=7
        )
        assert progress.lab_id == "2.1.3"
        assert progress.current_step == 2
        assert len(progress.completed_steps) == 2
    
    def test_progress_defaults(self):
        """Test progress defaults."""
        progress = StepProgress(lab_id="test", total_steps=5)
        assert progress.current_step == 0
        assert progress.completed_steps == []


class TestCommandMatch:
    """Tests for CommandMatch model."""
    
    def test_command_match_correct(self):
        """Test correct command match."""
        match = CommandMatch(
            expected="enable",
            actual="enable",
            is_correct=True,
            errors=[],
            suggestions=[]
        )
        assert match.is_correct
        assert len(match.errors) == 0
    
    def test_command_match_with_errors(self):
        """Test command match with errors."""
        match = CommandMatch(
            expected="hostname R1",
            actual="hostnam R1",
            is_correct=False,
            errors=["Typo in command: 'hostnam' should be 'hostname'"],
            suggestions=["Correct command: hostname R1"]
        )
        assert not match.is_correct
        assert len(match.errors) == 1
        assert "Typo" in match.errors[0]


class TestChatModels:
    """Tests for chat-related models."""
    
    def test_chat_request(self):
        """Test ChatRequest creation."""
        request = ChatRequest(
            message="How do I configure a hostname?",
            lab_id="2.1.3",
            step_id="3"
        )
        assert request.message == "How do I configure a hostname?"
        assert request.lab_id == "2.1.3"
    
    def test_chat_response(self):
        """Test ChatResponse creation."""
        response = ChatResponse(
            response="Use the hostname command",
            suggested_commands=["hostname R1"],
            current_step_hint="Configure the router hostname"
        )
        assert "hostname" in response.response
        assert len(response.suggested_commands) == 1
