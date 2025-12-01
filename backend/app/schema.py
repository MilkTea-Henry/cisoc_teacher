"""
Data models for lab schema.
Defines the structure for lab exercises, steps, and Q&A.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Command(BaseModel):
    """A CLI command with optional description."""
    cmd: str = Field(..., description="The CLI command string")
    description: Optional[str] = Field(None, description="Optional description of what this command does")


class ChecklistItem(BaseModel):
    """A single checklist item for verifying step completion."""
    item: str = Field(..., description="Description of the checklist item")
    required: bool = Field(True, description="Whether this item is required for completion")


class Step(BaseModel):
    """A single step in a lab exercise."""
    id: str = Field(..., description="Unique identifier for the step (e.g., '1.1', '2.3')")
    desc: str = Field(..., description="Description of the step")
    cmds: List[str] = Field(default_factory=list, description="List of CLI commands for this step")
    checklist: List[str] = Field(default_factory=list, description="Checklist items for verification")


class QA(BaseModel):
    """A question and answer pair for the lab."""
    q: str = Field(..., description="The question")
    a: str = Field(..., description="The answer")


class Lab(BaseModel):
    """Complete lab exercise schema."""
    lab_id: str = Field(..., description="Unique identifier for the lab")
    title: str = Field(..., description="Title of the lab exercise")
    chapter: Optional[str] = Field(None, description="Chapter number or identifier")
    objective: Optional[str] = Field(None, description="Learning objective of the lab")
    steps: List[Step] = Field(default_factory=list, description="Ordered list of steps")
    qa: List[QA] = Field(default_factory=list, description="Q&A pairs related to the lab")


class StepProgress(BaseModel):
    """Progress tracking for lab steps."""
    lab_id: str
    current_step: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    total_steps: int = 0


class CommandMatch(BaseModel):
    """Result of command matching/comparison."""
    expected: str = Field(..., description="Expected command")
    actual: str = Field(..., description="Actual command entered")
    is_correct: bool = Field(..., description="Whether the command matches")
    errors: List[str] = Field(default_factory=list, description="List of errors (typos, missing params)")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for correction")


class ChatMessage(BaseModel):
    """A chat message in the practice room."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat interaction."""
    message: str = Field(..., description="User message")
    lab_id: Optional[str] = Field(None, description="Current lab context")
    step_id: Optional[str] = Field(None, description="Current step context")


class ChatResponse(BaseModel):
    """Response from chat interaction."""
    response: str = Field(..., description="Assistant response")
    suggested_commands: List[str] = Field(default_factory=list, description="Suggested commands")
    current_step_hint: Optional[str] = Field(None, description="Hint for current step")
