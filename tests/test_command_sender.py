"""
Tests for command_sender module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.command_sender import (
    CommandSender,
    MockCommandSender,
    get_command_sender,
    set_command_sender
)


class TestCommandSender:
    """Tests for CommandSender class."""
    
    @pytest.fixture
    def sender(self):
        """Create a CommandSender instance."""
        return CommandSender()
    
    def test_sender_initialization(self, sender):
        """Test sender initialization."""
        assert sender.window_title == "Cisco Packet Tracer"
        # Automation might not be available in test environment
        # Just check the attribute exists
        assert hasattr(sender, 'automation_available')


class TestMockCommandSender:
    """Tests for MockCommandSender class."""
    
    @pytest.fixture
    def mock_sender(self):
        """Create a MockCommandSender instance."""
        return MockCommandSender()
    
    def test_mock_sender_creation(self, mock_sender):
        """Test mock sender creation."""
        assert mock_sender.automation_available
        assert mock_sender.sent_commands == []
        assert mock_sender.sent_keys == []
    
    def test_mock_send_command(self, mock_sender):
        """Test sending a command with mock."""
        result = mock_sender.send_command("enable")
        assert result
        assert "enable" in mock_sender.sent_commands
    
    def test_mock_send_multiple_commands(self, mock_sender):
        """Test sending multiple commands."""
        commands = ["enable", "configure terminal", "hostname R1"]
        results = mock_sender.send_commands(commands, delay_between=0)
        
        assert all(results)
        assert mock_sender.sent_commands == commands
    
    def test_mock_send_special_key(self, mock_sender):
        """Test sending special key."""
        result = mock_sender.send_special_key("enter")
        assert result
        assert "enter" in mock_sender.sent_keys
    
    def test_mock_send_ctrl_combination(self, mock_sender):
        """Test sending Ctrl combination."""
        result = mock_sender.send_ctrl_combination("c")
        assert result
        assert "ctrl+c" in mock_sender.sent_keys
    
    def test_mock_find_window(self, mock_sender):
        """Test mock window finding always returns True."""
        assert mock_sender.find_window()
    
    def test_mock_clear_commands(self, mock_sender):
        """Test clearing recorded commands."""
        mock_sender.send_command("test1")
        mock_sender.send_command("test2")
        mock_sender.send_special_key("enter")
        
        assert len(mock_sender.sent_commands) == 2
        assert len(mock_sender.sent_keys) == 1
        
        mock_sender.clear_sent_commands()
        
        assert mock_sender.sent_commands == []
        assert mock_sender.sent_keys == []


class TestGlobalSender:
    """Tests for global sender functions."""
    
    def test_get_command_sender(self):
        """Test getting global sender."""
        sender = get_command_sender()
        assert sender is not None
        assert isinstance(sender, CommandSender)
    
    def test_set_command_sender(self):
        """Test setting custom sender."""
        mock = MockCommandSender()
        set_command_sender(mock)
        sender = get_command_sender()
        assert sender is mock
        
        # Test it works
        sender.send_command("test")
        assert "test" in mock.sent_commands
        
        # Reset to default
        set_command_sender(CommandSender())


class TestCommandSenderIntegration:
    """Integration tests for command sender with mock."""
    
    def test_send_step_commands(self):
        """Test sending a sequence of step commands."""
        mock = MockCommandSender()
        set_command_sender(mock)
        
        # Simulate sending commands for a step
        step_commands = [
            "line console 0",
            "password cisco",
            "login",
            "exit"
        ]
        
        sender = get_command_sender()
        results = sender.send_commands(step_commands, delay_between=0)
        
        assert all(results)
        assert mock.sent_commands == step_commands
        
        # Reset
        set_command_sender(CommandSender())
    
    def test_send_with_enter(self):
        """Test that commands are sent with enter key."""
        mock = MockCommandSender()
        
        # The mock doesn't track enter key, but real implementation would
        result = mock.send_command("enable", press_enter=True)
        assert result
        assert "enable" in mock.sent_commands
