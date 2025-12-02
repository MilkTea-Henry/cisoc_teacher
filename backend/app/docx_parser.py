"""
DOCX Parser module.
Parses .docx lab files and extracts structured data including:
- Chapter/Section information
- Question numbers and titles
- Objectives
- Steps and procedures
- Key commands
- Scoring criteria
"""

import re
from typing import List, Optional, Tuple
from docx import Document
from docx.document import Document as DocxDocument

from .schema import Lab, Step, QA


def extract_chapter_info(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract chapter number and title from text.
    
    Args:
        text: Text to parse
        
    Returns:
        Tuple of (chapter_number, chapter_title)
    """
    # Pattern for chapter headers like "Chapter 1: Introduction" or "Ch.1 - Router Basics"
    patterns = [
        r'(?:Chapter|Ch\.?)\s*(\d+)[\s:：\-]+(.+)',
        r'第\s*(\d+)\s*章[\s:：\-]*(.+)',
        r'(\d+)\.\s*(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2).strip()
    
    return None, None


def extract_lab_id(text: str) -> Optional[str]:
    """
    Extract lab ID from text.
    
    Args:
        text: Text to parse
        
    Returns:
        Lab ID string or None
    """
    # Patterns for lab IDs like "Lab 2.1.3" or "實驗 1-2"
    patterns = [
        r'(?:Lab|實驗)\s*(\d+[\.\-]\d+(?:[\.\-]\d+)?)',
        r'(\d+[\.\-]\d+[\.\-]\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_objective(paragraphs: List[str]) -> Optional[str]:
    """
    Extract learning objective from paragraphs.
    
    Args:
        paragraphs: List of paragraph texts
        
    Returns:
        Objective text or None
    """
    objective_keywords = ['objective', 'goal', '目標', '學習目標', '實驗目標']
    
    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        for keyword in objective_keywords:
            if keyword in para_lower:
                # Return the text after the keyword, or next paragraph
                parts = re.split(r'[:：]', para, maxsplit=1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
                elif i + 1 < len(paragraphs):
                    return paragraphs[i + 1].strip()
    
    return None


def extract_steps(paragraphs: List[str]) -> List[Step]:
    """
    Extract steps from paragraphs.
    
    Args:
        paragraphs: List of paragraph texts
        
    Returns:
        List of Step objects
    """
    steps = []
    current_step = None
    current_cmds = []
    current_checklist = []
    
    # Patterns for step identification
    step_patterns = [
        r'^(?:Step|步驟)\s*(\d+(?:\.\d+)?)[\.:\s]+(.+)',
        r'^(\d+)\.\s+(.+)',
        r'^(\d+)\)\s+(.+)',
    ]
    
    # Pattern for commands (lines starting with Router>, Switch#, etc.)
    cmd_pattern = r'^(?:Router|Switch|R\d|S\d|[A-Za-z]+)(?:\([^\)]+\))?[>#]\s*(.+)'
    
    # Pattern for checklist items
    checklist_patterns = [
        r'^[\-\*\•]\s*(.+)',
        r'^(?:Check|確認|驗證)[\s:：]+(.+)',
    ]
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check for new step
        step_match = None
        for pattern in step_patterns:
            step_match = re.match(pattern, para, re.IGNORECASE)
            if step_match:
                break
        
        if step_match:
            # Save previous step
            if current_step:
                steps.append(Step(
                    id=current_step[0],
                    desc=current_step[1],
                    cmds=current_cmds,
                    checklist=current_checklist
                ))
            
            current_step = (step_match.group(1), step_match.group(2))
            current_cmds = []
            current_checklist = []
            continue
        
        # Check for commands
        cmd_match = re.match(cmd_pattern, para)
        if cmd_match and current_step:
            current_cmds.append(cmd_match.group(1).strip())
            continue
        
        # Also check for indented commands (common in labs)
        if para.startswith('  ') and current_step:
            cmd_text = para.strip()
            # Filter out obvious non-commands
            if not any(cmd_text.lower().startswith(x) for x in ['note:', '注意:', 'hint:', '提示:']):
                if len(cmd_text) < 100:  # Commands are usually short
                    current_cmds.append(cmd_text)
            continue
        
        # Check for checklist items
        for pattern in checklist_patterns:
            checklist_match = re.match(pattern, para)
            if checklist_match and current_step:
                current_checklist.append(checklist_match.group(1).strip())
                break
    
    # Save last step
    if current_step:
        steps.append(Step(
            id=current_step[0],
            desc=current_step[1],
            cmds=current_cmds,
            checklist=current_checklist
        ))
    
    return steps


def extract_qa(paragraphs: List[str]) -> List[QA]:
    """
    Extract Q&A pairs from paragraphs.
    
    Args:
        paragraphs: List of paragraph texts
        
    Returns:
        List of QA objects
    """
    qa_list = []
    current_question = None
    
    # Patterns for questions
    q_patterns = [
        r'^(?:Q|問題|Question)\s*\d*[\.\:：]?\s*(.+)',
        r'^\d+\.\s*(.+\?)\s*$',
    ]
    
    # Patterns for answers
    a_patterns = [
        r'^(?:A|答案|Answer)\s*\d*[\.\:：]?\s*(.+)',
    ]
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check for questions
        for pattern in q_patterns:
            q_match = re.match(pattern, para, re.IGNORECASE)
            if q_match:
                current_question = q_match.group(1).strip()
                break
        
        if current_question:
            # Check for answers
            for pattern in a_patterns:
                a_match = re.match(pattern, para, re.IGNORECASE)
                if a_match:
                    qa_list.append(QA(q=current_question, a=a_match.group(1).strip()))
                    current_question = None
                    break
    
    return qa_list


def parse_docx(file_path: str) -> Lab:
    """
    Parse a .docx file and extract lab information.
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        Lab object with extracted data
    """
    doc: DocxDocument = Document(file_path)
    
    # Extract all paragraph texts
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    
    # Get the full text for initial parsing
    full_text = '\n'.join(paragraphs)
    
    # Extract basic info
    lab_id = extract_lab_id(full_text) or "unknown"
    chapter, title = extract_chapter_info(full_text)
    
    # If no title found, use first non-empty paragraph
    if not title and paragraphs:
        title = paragraphs[0]
    
    objective = extract_objective(paragraphs)
    steps = extract_steps(paragraphs)
    qa = extract_qa(paragraphs)
    
    return Lab(
        lab_id=lab_id,
        title=title or "Untitled Lab",
        chapter=chapter,
        objective=objective,
        steps=steps,
        qa=qa
    )


def parse_docx_to_json(file_path: str) -> str:
    """
    Parse a .docx file and return JSON string.
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        JSON string representation of the lab
    """
    lab = parse_docx(file_path)
    return lab.model_dump_json(indent=2)
