"""
Command Sender module.
Provides functionality to send commands to the Cisco Packet Tracer CLI window.
"""

import time
from typing import Optional, List


class CommandSender:
    """
    Sends commands to the Cisco Packet Tracer CLI window.
    Uses keyboard automation to input commands.
    """
    
    def __init__(self, window_title: str = "Cisco Packet Tracer"):
        """
        Initialize the command sender.
        
        Args:
            window_title: Title of the Packet Tracer window
        """
        self.window_title = window_title
        self.automation_available = False
        self._init_automation()
    
    def _init_automation(self):
        """Initialize automation dependencies."""
        try:
            import pyautogui
            import pygetwindow as gw
            self.automation_available = True
        except ImportError:
            self.automation_available = False
            print("Warning: Automation dependencies not available. Install pyautogui and pygetwindow.")
    
    def find_window(self) -> bool:
        """
        Find and focus the Packet Tracer window.
        
        Returns:
            True if window found and focused, False otherwise
        """
        if not self.automation_available:
            return False
        
        try:
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                win.activate()
                time.sleep(0.2)  # Wait for window to focus
                return True
        except Exception as e:
            print(f"Error finding window: {e}")
        
        return False
    
    def send_command(
        self,
        command: str,
        press_enter: bool = True,
        delay: float = 0.05
    ) -> bool:
        """
        Send a command to the CLI window.
        
        Args:
            command: Command string to send
            press_enter: Whether to press Enter after the command
            delay: Delay between keystrokes in seconds
            
        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.automation_available:
            return False
        
        try:
            import pyautogui
            
            # Focus the window
            if not self.find_window():
                return False
            
            # Type the command
            pyautogui.typewrite(command, interval=delay)
            
            # Press Enter if requested
            if press_enter:
                pyautogui.press('enter')
            
            return True
            
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def send_commands(
        self,
        commands: List[str],
        delay_between: float = 0.5
    ) -> List[bool]:
        """
        Send multiple commands to the CLI.
        
        Args:
            commands: List of commands to send
            delay_between: Delay between commands in seconds
            
        Returns:
            List of success/failure for each command
        """
        results = []
        
        for cmd in commands:
            success = self.send_command(cmd)
            results.append(success)
            time.sleep(delay_between)
        
        return results
    
    def send_special_key(self, key: str) -> bool:
        """
        Send a special key to the CLI.
        
        Args:
            key: Key name (e.g., 'enter', 'tab', 'escape', 'f1')
            
        Returns:
            True if key sent successfully, False otherwise
        """
        if not self.automation_available:
            return False
        
        try:
            import pyautogui
            
            if not self.find_window():
                return False
            
            pyautogui.press(key)
            return True
            
        except Exception as e:
            print(f"Error sending special key: {e}")
            return False
    
    def send_ctrl_combination(self, key: str) -> bool:
        """
        Send a Ctrl+key combination.
        
        Args:
            key: Key to combine with Ctrl (e.g., 'c' for Ctrl+C)
            
        Returns:
            True if combination sent successfully, False otherwise
        """
        if not self.automation_available:
            return False
        
        try:
            import pyautogui
            
            if not self.find_window():
                return False
            
            pyautogui.hotkey('ctrl', key)
            return True
            
        except Exception as e:
            print(f"Error sending Ctrl combination: {e}")
            return False
    
    def clear_line(self) -> bool:
        """
        Clear the current command line.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.automation_available:
            return False
        
        try:
            import pyautogui
            
            if not self.find_window():
                return False
            
            # Select all and delete
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            return True
            
        except Exception as e:
            print(f"Error clearing line: {e}")
            return False


class MockCommandSender(CommandSender):
    """
    Mock command sender for testing.
    Records commands without actually sending them.
    """
    
    def __init__(self):
        super().__init__()
        self.automation_available = True  # Pretend automation is available
        self.sent_commands: List[str] = []
        self.sent_keys: List[str] = []
    
    def find_window(self) -> bool:
        """Always return True for mock."""
        return True
    
    def send_command(
        self,
        command: str,
        press_enter: bool = True,
        delay: float = 0.05
    ) -> bool:
        """Record command instead of sending."""
        self.sent_commands.append(command)
        return True
    
    def send_special_key(self, key: str) -> bool:
        """Record key instead of sending."""
        self.sent_keys.append(key)
        return True
    
    def send_ctrl_combination(self, key: str) -> bool:
        """Record combination instead of sending."""
        self.sent_keys.append(f"ctrl+{key}")
        return True
    
    def clear_sent_commands(self) -> None:
        """Clear recorded commands."""
        self.sent_commands.clear()
        self.sent_keys.clear()


# Global sender instance
_command_sender: Optional[CommandSender] = None


def get_command_sender() -> CommandSender:
    """Get or create the global command sender instance."""
    global _command_sender
    if _command_sender is None:
        _command_sender = CommandSender()
    return _command_sender


def set_command_sender(sender: CommandSender) -> None:
    """Set a custom command sender (useful for testing)."""
    global _command_sender
    _command_sender = sender
