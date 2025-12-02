"""
CLI Watcher module.
Monitors Cisco Packet Tracer CLI window using OCR (Optical Character Recognition)
and provides real-time command comparison and error detection.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from difflib import SequenceMatcher

from .schema import CommandMatch


class CLIWatcher:
    """
    Watches and monitors Cisco Packet Tracer CLI window.
    Uses OCR to detect text and compares commands against expected values.
    """
    
    def __init__(self, window_title: str = "Cisco Packet Tracer"):
        """
        Initialize the CLI watcher.
        
        Args:
            window_title: Title of the Packet Tracer window to monitor
        """
        self.window_title = window_title
        self.ocr_available = False
        self.last_captured_text = ""
        self.command_history: List[str] = []
        
        # Try to initialize OCR
        self._init_ocr()
    
    def _init_ocr(self):
        """Initialize OCR dependencies."""
        try:
            import pytesseract
            import mss
            from PIL import Image
            self.ocr_available = True
        except ImportError:
            self.ocr_available = False
            print("Warning: OCR dependencies not available. Install pytesseract, mss, and pillow.")
    
    def find_cli_window(self) -> Optional[Dict[str, int]]:
        """
        Find the Cisco Packet Tracer CLI window.
        
        Returns:
            Window bounds dict with 'left', 'top', 'width', 'height' or None
        """
        try:
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                return {
                    "left": win.left,
                    "top": win.top,
                    "width": win.width,
                    "height": win.height
                }
        except Exception:
            pass
        
        return None
    
    def capture_cli_text(self, region: Optional[Dict[str, int]] = None) -> str:
        """
        Capture text from the CLI window using OCR.
        
        Args:
            region: Optional region to capture. If None, tries to find the window.
            
        Returns:
            Captured text from the CLI window
        """
        if not self.ocr_available:
            return ""
        
        try:
            import pytesseract
            import mss
            from PIL import Image
            
            if region is None:
                region = self.find_cli_window()
            
            if region is None:
                return ""
            
            # Capture screenshot
            with mss.mss() as sct:
                monitor = {
                    "left": region["left"],
                    "top": region["top"],
                    "width": region["width"],
                    "height": region["height"]
                }
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Process image for better OCR
            # Convert to grayscale and increase contrast
            img = img.convert('L')
            
            # Run OCR
            text = pytesseract.image_to_string(img)
            self.last_captured_text = text
            
            return text
            
        except Exception as e:
            print(f"Error capturing CLI text: {e}")
            return ""
    
    def extract_commands(self, cli_text: str) -> List[str]:
        """
        Extract commands from CLI text output.
        
        Args:
            cli_text: Raw text from CLI
            
        Returns:
            List of extracted commands
        """
        commands = []
        
        # Pattern to match CLI prompts and commands
        # Matches: Router>, Router#, Switch>, S1#, R1(config)#, etc.
        prompt_pattern = r'^([A-Za-z0-9_\-]+(?:\([^\)]+\))?[>#])\s*(.+)$'
        
        lines = cli_text.split('\n')
        for line in lines:
            line = line.strip()
            match = re.match(prompt_pattern, line)
            if match:
                command = match.group(2).strip()
                if command and command not in ['', ' ']:
                    commands.append(command)
        
        return commands
    
    def get_latest_command(self, cli_text: str) -> Optional[str]:
        """
        Get the most recent command from CLI text.
        
        Args:
            cli_text: Raw text from CLI
            
        Returns:
            Most recent command or None
        """
        commands = self.extract_commands(cli_text)
        return commands[-1] if commands else None
    
    def compare_commands(self, expected: str, actual: str) -> CommandMatch:
        """
        Compare expected and actual commands, detecting errors.
        
        Args:
            expected: Expected command string
            actual: Actual command string entered
            
        Returns:
            CommandMatch object with comparison results
        """
        errors = []
        suggestions = []
        
        # Normalize commands for comparison
        expected_norm = expected.lower().strip()
        actual_norm = actual.lower().strip()
        
        # Check for exact match
        if expected_norm == actual_norm:
            return CommandMatch(
                expected=expected,
                actual=actual,
                is_correct=True,
                errors=[],
                suggestions=[]
            )
        
        # Calculate similarity
        similarity = SequenceMatcher(None, expected_norm, actual_norm).ratio()
        
        # Detect specific error types
        expected_parts = expected_norm.split()
        actual_parts = actual_norm.split()
        
        # Check for typos in command keyword
        if expected_parts and actual_parts:
            if expected_parts[0] != actual_parts[0]:
                if SequenceMatcher(None, expected_parts[0], actual_parts[0]).ratio() > 0.7:
                    errors.append(f"Typo in command: '{actual_parts[0]}' should be '{expected_parts[0]}'")
                else:
                    errors.append(f"Wrong command: expected '{expected_parts[0]}'")
        
        # Check for missing parameters
        expected_params = set(expected_parts[1:]) if len(expected_parts) > 1 else set()
        actual_params = set(actual_parts[1:]) if len(actual_parts) > 1 else set()
        
        missing_params = expected_params - actual_params
        extra_params = actual_params - expected_params
        
        if missing_params:
            errors.append(f"Missing parameters: {', '.join(missing_params)}")
            suggestions.append(f"Add: {' '.join(missing_params)}")
        
        if extra_params:
            errors.append(f"Extra parameters: {', '.join(extra_params)}")
        
        # Check for parameter order issues
        if len(expected_parts) == len(actual_parts) and not errors:
            for i, (exp, act) in enumerate(zip(expected_parts, actual_parts)):
                if exp != act:
                    sim = SequenceMatcher(None, exp, act).ratio()
                    if sim > 0.5:
                        errors.append(f"Possible typo at position {i + 1}: '{act}' → '{exp}'")
        
        # Provide suggestion for correction
        if errors:
            suggestions.append(f"Correct command: {expected}")
        
        # Consider it correct if similarity is very high (> 0.95)
        is_correct = similarity > 0.95
        
        return CommandMatch(
            expected=expected,
            actual=actual,
            is_correct=is_correct,
            errors=errors,
            suggestions=suggestions
        )
    
    def analyze_cli_output(
        self,
        cli_text: str,
        expected_commands: List[str]
    ) -> List[CommandMatch]:
        """
        Analyze CLI output against expected commands.
        
        Args:
            cli_text: Raw CLI text from OCR
            expected_commands: List of expected commands
            
        Returns:
            List of CommandMatch objects for each comparison
        """
        actual_commands = self.extract_commands(cli_text)
        results = []
        
        # Match actual commands with expected ones
        for actual in actual_commands:
            best_match = None
            best_score = 0
            
            for expected in expected_commands:
                score = SequenceMatcher(None, expected.lower(), actual.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = expected
            
            if best_match and best_score > 0.3:
                results.append(self.compare_commands(best_match, actual))
            else:
                # Unknown command
                results.append(CommandMatch(
                    expected="(unknown)",
                    actual=actual,
                    is_correct=False,
                    errors=["Command not recognized in current step"],
                    suggestions=["Check if you're on the correct step"]
                ))
        
        return results
    
    def start_watching(self, interval: float = 1.0) -> None:
        """
        Start continuous CLI monitoring.
        
        Args:
            interval: Time between captures in seconds
        """
        # This would typically run in a separate thread/process
        # For now, this is a placeholder for the watching loop
        import time
        
        while True:
            text = self.capture_cli_text()
            if text != self.last_captured_text:
                self.last_captured_text = text
                # Process new text...
            time.sleep(interval)
    
    def stop_watching(self) -> None:
        """Stop CLI monitoring."""
        # Placeholder for stopping the watch loop
        pass


class MockCLIWatcher(CLIWatcher):
    """
    Mock CLI watcher for testing purposes.
    Simulates CLI capture without actual OCR.
    """
    
    def __init__(self, mock_text: str = ""):
        super().__init__()
        self.mock_text = mock_text
        self.ocr_available = True  # Pretend OCR is available
    
    def set_mock_text(self, text: str) -> None:
        """Set the mock CLI text."""
        self.mock_text = text
    
    def capture_cli_text(self, region: Optional[Dict[str, int]] = None) -> str:
        """Return mock text instead of actual OCR."""
        return self.mock_text
    
    def find_cli_window(self) -> Optional[Dict[str, int]]:
        """Return fake window bounds."""
        return {"left": 0, "top": 0, "width": 800, "height": 600}


# Global watcher instance
_cli_watcher: Optional[CLIWatcher] = None


def get_cli_watcher() -> CLIWatcher:
    """Get or create the global CLI watcher instance."""
    global _cli_watcher
    if _cli_watcher is None:
        _cli_watcher = CLIWatcher()
    return _cli_watcher


def set_cli_watcher(watcher: CLIWatcher) -> None:
    """Set a custom CLI watcher (useful for testing)."""
    global _cli_watcher
    _cli_watcher = watcher
