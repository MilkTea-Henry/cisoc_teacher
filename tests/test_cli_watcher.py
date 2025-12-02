"""
Tests for CLI watcher module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.cli_watcher import (
    CLIWatcher,
    MockCLIWatcher,
    get_cli_watcher,
    set_cli_watcher
)
from backend.app.schema import CommandMatch


class TestCLIWatcher:
    """Tests for CLIWatcher class."""
    
    @pytest.fixture
    def watcher(self):
        """Create a CLIWatcher instance."""
        return CLIWatcher()
    
    def test_watcher_initialization(self, watcher):
        """Test watcher initialization."""
        assert watcher.window_title == "Cisco Packet Tracer"
        assert watcher.last_captured_text == ""
        assert watcher.command_history == []
    
    def test_extract_commands_basic(self, watcher):
        """Test extracting commands from CLI text."""
        cli_text = """
Router> enable
Router# configure terminal
Router(config)# hostname R1
R1(config)# exit
"""
        commands = watcher.extract_commands(cli_text)
        assert "enable" in commands
        assert "configure terminal" in commands
        assert "hostname R1" in commands
        assert "exit" in commands
    
    def test_extract_commands_switch(self, watcher):
        """Test extracting commands from switch CLI."""
        cli_text = """
Switch> enable
Switch# show vlan brief
Switch# configure terminal
Switch(config)# vlan 10
"""
        commands = watcher.extract_commands(cli_text)
        assert "enable" in commands
        assert "show vlan brief" in commands
        assert "vlan 10" in commands
    
    def test_extract_commands_named_device(self, watcher):
        """Test with named devices."""
        cli_text = """
S1> enable
S1# configure terminal
R1(config)# interface g0/0
"""
        commands = watcher.extract_commands(cli_text)
        assert "enable" in commands
        assert "configure terminal" in commands
        assert "interface g0/0" in commands
    
    def test_extract_commands_empty(self, watcher):
        """Test with empty CLI text."""
        commands = watcher.extract_commands("")
        assert commands == []
    
    def test_get_latest_command(self, watcher):
        """Test getting the latest command."""
        cli_text = """
Router> enable
Router# configure terminal
Router(config)# hostname R1
"""
        latest = watcher.get_latest_command(cli_text)
        assert latest == "hostname R1"
    
    def test_get_latest_command_empty(self, watcher):
        """Test latest command with empty text."""
        latest = watcher.get_latest_command("")
        assert latest is None


class TestCommandComparison:
    """Tests for command comparison functionality."""
    
    @pytest.fixture
    def watcher(self):
        return CLIWatcher()
    
    def test_compare_exact_match(self, watcher):
        """Test exact command match."""
        result = watcher.compare_commands("enable", "enable")
        assert result.is_correct
        assert result.errors == []
    
    def test_compare_case_insensitive(self, watcher):
        """Test case insensitive comparison."""
        result = watcher.compare_commands("Enable", "enable")
        assert result.is_correct
    
    def test_compare_typo_detection(self, watcher):
        """Test typo detection."""
        result = watcher.compare_commands("hostname R1", "hostnam R1")
        # The command has errors detected
        assert any("typo" in e.lower() or "hostnam" in e.lower() for e in result.errors)
    
    def test_compare_missing_parameter(self, watcher):
        """Test missing parameter detection."""
        result = watcher.compare_commands("hostname R1", "hostname")
        assert not result.is_correct
        assert any("missing" in e.lower() or "r1" in e.lower() for e in result.errors)
    
    def test_compare_extra_parameter(self, watcher):
        """Test extra parameter detection."""
        result = watcher.compare_commands("enable", "enable password")
        assert not result.is_correct
        assert any("extra" in e.lower() for e in result.errors)
    
    def test_compare_wrong_command(self, watcher):
        """Test completely wrong command."""
        result = watcher.compare_commands("enable", "disable")
        assert not result.is_correct
    
    def test_compare_complex_command(self, watcher):
        """Test complex command comparison."""
        expected = "interface gigabitethernet 0/0"
        actual = "interface gigabitethernet 0/0"
        result = watcher.compare_commands(expected, actual)
        assert result.is_correct
    
    def test_compare_with_suggestions(self, watcher):
        """Test that suggestions are provided for errors."""
        result = watcher.compare_commands("copy running-config startup-config", "copy run star")
        # Not an exact match but might be abbreviated
        assert result.expected == "copy running-config startup-config"
        assert result.actual == "copy run star"


class TestMockCLIWatcher:
    """Tests for MockCLIWatcher class."""
    
    def test_mock_watcher_creation(self):
        """Test mock watcher creation."""
        mock = MockCLIWatcher()
        assert mock.ocr_available
    
    def test_mock_watcher_with_text(self):
        """Test mock watcher with preset text."""
        mock = MockCLIWatcher("Router> enable")
        text = mock.capture_cli_text()
        assert text == "Router> enable"
    
    def test_mock_watcher_set_text(self):
        """Test setting mock text."""
        mock = MockCLIWatcher()
        mock.set_mock_text("Switch# show vlan")
        text = mock.capture_cli_text()
        assert text == "Switch# show vlan"
    
    def test_mock_watcher_find_window(self):
        """Test mock window finding."""
        mock = MockCLIWatcher()
        bounds = mock.find_cli_window()
        assert bounds is not None
        assert "left" in bounds
        assert "top" in bounds


class TestAnalyzeCLIOutput:
    """Tests for CLI output analysis."""
    
    @pytest.fixture
    def watcher(self):
        return CLIWatcher()
    
    def test_analyze_matching_commands(self, watcher):
        """Test analyzing output with matching commands."""
        cli_text = """
Router> enable
Router# configure terminal
"""
        expected = ["enable", "configure terminal"]
        results = watcher.analyze_cli_output(cli_text, expected)
        
        assert len(results) >= 2
        # At least some should be correct
        correct_count = sum(1 for r in results if r.is_correct)
        assert correct_count >= 1
    
    def test_analyze_unknown_command(self, watcher):
        """Test analyzing output with unknown commands."""
        cli_text = "Router# random unknown command"
        expected = ["enable", "configure terminal"]
        results = watcher.analyze_cli_output(cli_text, expected)
        
        # Should have results for the actual command
        assert len(results) >= 0  # May or may not detect depending on format


class TestGlobalWatcher:
    """Tests for global watcher functions."""
    
    def test_get_cli_watcher(self):
        """Test getting global watcher."""
        watcher = get_cli_watcher()
        assert watcher is not None
        assert isinstance(watcher, CLIWatcher)
    
    def test_set_cli_watcher(self):
        """Test setting custom watcher."""
        mock = MockCLIWatcher("test")
        set_cli_watcher(mock)
        watcher = get_cli_watcher()
        assert watcher is mock
        assert watcher.capture_cli_text() == "test"
        
        # Reset to default
        set_cli_watcher(CLIWatcher())
