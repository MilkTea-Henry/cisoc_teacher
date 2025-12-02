"""
Main FastAPI application for Cisco Lab Teacher.
Provides REST API endpoints for lab management, chat, and CLI interaction.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .schema import (
    Lab, Step, StepProgress, CommandMatch, 
    ChatRequest, ChatResponse, QA
)
from .docx_parser import parse_docx, parse_docx_to_json
from .rag import get_rag_engine, RAGEngine
from .cli_watcher import get_cli_watcher, CLIWatcher
from .command_sender import get_command_sender, CommandSender

# Create FastAPI app
app = FastAPI(
    title="Cisco Lab Teacher API",
    description="API for Cisco lab exercises with RAG-based Q&A and CLI monitoring",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for labs and progress
labs_storage: dict[str, Lab] = {}
progress_storage: dict[str, StepProgress] = {}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Cisco Lab Teacher API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============ Lab Management Endpoints ============

@app.post("/labs/upload", response_model=Lab)
async def upload_lab(file: UploadFile = File(...)):
    """
    Upload a .docx lab file and parse it.
    
    Args:
        file: The .docx file to upload
        
    Returns:
        Parsed Lab object
    """
    if not file.filename or not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="File must be a .docx file")
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    try:
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Parse the docx file
        lab = parse_docx(temp_path)
        
        # Store the lab
        labs_storage[lab.lab_id] = lab
        
        # Load into RAG engine
        rag_engine = get_rag_engine()
        rag_engine.load_lab(lab)
        
        return lab
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/labs/json", response_model=Lab)
async def load_lab_json(lab: Lab):
    """
    Load a lab from JSON directly.
    
    Args:
        lab: Lab object in JSON format
        
    Returns:
        Loaded Lab object
    """
    labs_storage[lab.lab_id] = lab
    
    # Load into RAG engine
    rag_engine = get_rag_engine()
    rag_engine.load_lab(lab)
    
    return lab


@app.get("/labs", response_model=List[Lab])
async def list_labs():
    """
    List all loaded labs.
    
    Returns:
        List of Lab objects
    """
    return list(labs_storage.values())


@app.get("/labs/{lab_id}", response_model=Lab)
async def get_lab(lab_id: str):
    """
    Get a specific lab by ID.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        Lab object
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    return labs_storage[lab_id]


@app.get("/labs/{lab_id}/json")
async def get_lab_json(lab_id: str):
    """
    Get a lab as JSON string.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        JSON string of the lab
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    return JSONResponse(content=labs_storage[lab_id].model_dump())


@app.delete("/labs/{lab_id}")
async def delete_lab(lab_id: str):
    """
    Delete a lab.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        Success message
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    del labs_storage[lab_id]
    return {"message": f"Lab '{lab_id}' deleted"}


# ============ Step Progress Endpoints ============

@app.get("/labs/{lab_id}/progress", response_model=StepProgress)
async def get_progress(lab_id: str):
    """
    Get progress for a lab.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        StepProgress object
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    if lab_id not in progress_storage:
        lab = labs_storage[lab_id]
        progress_storage[lab_id] = StepProgress(
            lab_id=lab_id,
            current_step=0,
            completed_steps=[],
            total_steps=len(lab.steps)
        )
    
    return progress_storage[lab_id]


@app.post("/labs/{lab_id}/progress/next")
async def advance_step(lab_id: str):
    """
    Advance to the next step.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        Updated StepProgress
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    progress = await get_progress(lab_id)
    lab = labs_storage[lab_id]
    
    if progress.current_step < len(lab.steps):
        current_step_id = lab.steps[progress.current_step].id
        if current_step_id not in progress.completed_steps:
            progress.completed_steps.append(current_step_id)
        progress.current_step += 1
    
    return progress


@app.post("/labs/{lab_id}/progress/complete/{step_id}")
async def complete_step(lab_id: str, step_id: str):
    """
    Mark a specific step as complete.
    
    Args:
        lab_id: Lab identifier
        step_id: Step identifier
        
    Returns:
        Updated StepProgress
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    progress = await get_progress(lab_id)
    
    if step_id not in progress.completed_steps:
        progress.completed_steps.append(step_id)
    
    return progress


@app.post("/labs/{lab_id}/progress/reset")
async def reset_progress(lab_id: str):
    """
    Reset progress for a lab.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        Reset StepProgress
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    lab = labs_storage[lab_id]
    progress_storage[lab_id] = StepProgress(
        lab_id=lab_id,
        current_step=0,
        completed_steps=[],
        total_steps=len(lab.steps)
    )
    
    return progress_storage[lab_id]


# ============ Chat/RAG Endpoints ============

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant about labs.
    
    Args:
        request: Chat request with message and optional context
        
    Returns:
        ChatResponse with answer and suggestions
    """
    rag_engine = get_rag_engine()
    
    response = rag_engine.answer_question(
        question=request.message,
        lab_id=request.lab_id,
        step_id=request.step_id
    )
    
    return response


@app.get("/search")
async def search(query: str, lab_id: Optional[str] = None, k: int = 5):
    """
    Search lab content.
    
    Args:
        query: Search query
        lab_id: Optional lab to search within
        k: Number of results to return
        
    Returns:
        Search results
    """
    rag_engine = get_rag_engine()
    results = rag_engine.search(query, k=k)
    
    if lab_id:
        results = [r for r in results if r["metadata"].get("lab_id") == lab_id]
    
    return {"results": results}


# ============ CLI Monitoring Endpoints ============

@app.get("/cli/capture")
async def capture_cli():
    """
    Capture current CLI window text.
    
    Returns:
        Captured text
    """
    watcher = get_cli_watcher()
    text = watcher.capture_cli_text()
    return {"text": text, "commands": watcher.extract_commands(text)}


@app.post("/cli/compare", response_model=CommandMatch)
async def compare_command(expected: str, actual: str):
    """
    Compare expected and actual commands.
    
    Args:
        expected: Expected command
        actual: Actual command entered
        
    Returns:
        CommandMatch with comparison results
    """
    watcher = get_cli_watcher()
    return watcher.compare_commands(expected, actual)


@app.post("/cli/analyze")
async def analyze_cli(expected_commands: List[str]):
    """
    Analyze CLI output against expected commands.
    
    Args:
        expected_commands: List of expected commands
        
    Returns:
        Analysis results
    """
    watcher = get_cli_watcher()
    text = watcher.capture_cli_text()
    results = watcher.analyze_cli_output(text, expected_commands)
    return {"results": [r.model_dump() for r in results]}


# ============ Command Sending Endpoints ============

@app.post("/cli/send")
async def send_command(command: str, press_enter: bool = True):
    """
    Send a command to the CLI window.
    
    Args:
        command: Command to send
        press_enter: Whether to press Enter after
        
    Returns:
        Success status
    """
    sender = get_command_sender()
    success = sender.send_command(command, press_enter=press_enter)
    return {"success": success, "command": command}


@app.post("/cli/send-step")
async def send_step_commands(lab_id: str, step_id: str):
    """
    Send all commands for a specific step.
    
    Args:
        lab_id: Lab identifier
        step_id: Step identifier
        
    Returns:
        Send results
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    lab = labs_storage[lab_id]
    step = None
    for s in lab.steps:
        if s.id == step_id:
            step = s
            break
    
    if step is None:
        raise HTTPException(status_code=404, detail=f"Step '{step_id}' not found")
    
    sender = get_command_sender()
    results = sender.send_commands(step.cmds)
    
    return {
        "step_id": step_id,
        "commands": step.cmds,
        "results": results
    }


# ============ Step Hints Endpoints ============

@app.get("/labs/{lab_id}/steps/{step_id}/hint")
async def get_step_hint(lab_id: str, step_id: str):
    """
    Get hint for a specific step.
    
    Args:
        lab_id: Lab identifier
        step_id: Step identifier
        
    Returns:
        Step hint and commands
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    lab = labs_storage[lab_id]
    for step in lab.steps:
        if step.id == step_id:
            return {
                "step_id": step_id,
                "description": step.desc,
                "commands": step.cmds,
                "checklist": step.checklist
            }
    
    raise HTTPException(status_code=404, detail=f"Step '{step_id}' not found")


@app.get("/labs/{lab_id}/current-hint")
async def get_current_hint(lab_id: str):
    """
    Get hint for current step based on progress.
    
    Args:
        lab_id: Lab identifier
        
    Returns:
        Current step hint
    """
    if lab_id not in labs_storage:
        raise HTTPException(status_code=404, detail=f"Lab '{lab_id}' not found")
    
    progress = await get_progress(lab_id)
    lab = labs_storage[lab_id]
    
    if progress.current_step >= len(lab.steps):
        return {
            "message": "Lab completed!",
            "step_id": None,
            "description": "You have completed all steps in this lab.",
            "commands": [],
            "checklist": []
        }
    
    current_step = lab.steps[progress.current_step]
    return {
        "step_id": current_step.id,
        "description": current_step.desc,
        "commands": current_step.cmds,
        "checklist": current_step.checklist,
        "progress": {
            "current": progress.current_step + 1,
            "total": progress.total_steps
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
