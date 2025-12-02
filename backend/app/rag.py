"""
RAG (Retrieval Augmented Generation) module.
Provides vector-based search and Q&A functionality for lab content.
"""

import json
import os
from typing import List, Optional, Dict, Any

from .schema import Lab, ChatResponse


class RAGEngine:
    """
    RAG engine for lab content retrieval and Q&A.
    Uses FAISS for vector storage and sentence transformers for embeddings.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG engine.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.labs: Dict[str, Lab] = {}
        self.embeddings = None
        self.vectorstore = None
        self.documents: List[Dict[str, Any]] = []
        self._initialized = False
    
    def _lazy_init(self):
        """Lazy initialization of heavy dependencies."""
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            self._initialized = True
        except ImportError as e:
            # Graceful degradation - RAG features won't work but app still runs
            print(f"Warning: RAG dependencies not available: {e}")
            self._initialized = False
    
    def load_lab(self, lab: Lab) -> None:
        """
        Load a lab into the RAG engine.
        
        Args:
            lab: Lab object to load
        """
        self.labs[lab.lab_id] = lab
        
        # Create documents for indexing
        # Index steps
        for step in lab.steps:
            doc = {
                "content": f"Step {step.id}: {step.desc}. Commands: {', '.join(step.cmds)}",
                "metadata": {
                    "lab_id": lab.lab_id,
                    "step_id": step.id,
                    "type": "step"
                }
            }
            self.documents.append(doc)
        
        # Index Q&A
        for qa in lab.qa:
            doc = {
                "content": f"Question: {qa.q} Answer: {qa.a}",
                "metadata": {
                    "lab_id": lab.lab_id,
                    "type": "qa"
                }
            }
            self.documents.append(doc)
        
        # Index objective
        if lab.objective:
            doc = {
                "content": f"Lab {lab.lab_id} - {lab.title}. Objective: {lab.objective}",
                "metadata": {
                    "lab_id": lab.lab_id,
                    "type": "objective"
                }
            }
            self.documents.append(doc)
    
    def load_from_json(self, json_path: str) -> Lab:
        """
        Load a lab from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            Loaded Lab object
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        lab = Lab(**data)
        self.load_lab(lab)
        return lab
    
    def build_index(self) -> None:
        """Build the vector index from loaded documents."""
        self._lazy_init()
        
        if not self._initialized or not self.documents:
            return
        
        try:
            from langchain_community.vectorstores import FAISS
            from langchain.schema import Document
            
            docs = [
                Document(page_content=d["content"], metadata=d["metadata"])
                for d in self.documents
            ]
            
            self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        except Exception as e:
            print(f"Warning: Could not build vector index: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching documents with scores
        """
        if not self.vectorstore:
            # Fallback to simple keyword search
            return self._keyword_search(query, k)
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]
        except Exception:
            return self._keyword_search(query, k)
    
    def _keyword_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search fallback.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Simple scoring based on word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            
            if overlap > 0:
                scored_docs.append((doc, overlap))
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": score
            }
            for doc, score in scored_docs[:k]
        ]
    
    def answer_question(
        self,
        question: str,
        lab_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            lab_id: Optional lab context
            step_id: Optional step context
            
        Returns:
            ChatResponse with answer and suggestions
        """
        # Search for relevant content
        results = self.search(question)
        
        # Filter by lab_id if provided
        if lab_id:
            results = [r for r in results if r["metadata"].get("lab_id") == lab_id]
        
        # Build context from results
        context_parts = [r["content"] for r in results[:3]]
        context = "\n".join(context_parts)
        
        # Generate response
        if results:
            # Use the most relevant result as the base for the answer
            top_result = results[0]
            
            if top_result["metadata"].get("type") == "qa":
                # Direct Q&A match
                response = top_result["content"].split("Answer: ")[-1]
            elif top_result["metadata"].get("type") == "step":
                # Step information
                response = f"Based on the lab content: {top_result['content']}"
            else:
                response = f"Here's what I found: {top_result['content']}"
        else:
            response = "I couldn't find specific information about that. Could you please rephrase your question or provide more context?"
        
        # Get suggested commands if in step context
        suggested_commands = []
        current_step_hint = None
        
        if lab_id and step_id and lab_id in self.labs:
            lab = self.labs[lab_id]
            for step in lab.steps:
                if step.id == step_id:
                    suggested_commands = step.cmds
                    current_step_hint = step.desc
                    break
        
        return ChatResponse(
            response=response,
            suggested_commands=suggested_commands,
            current_step_hint=current_step_hint
        )
    
    def get_step_commands(self, lab_id: str, step_id: str) -> List[str]:
        """
        Get commands for a specific step.
        
        Args:
            lab_id: Lab identifier
            step_id: Step identifier
            
        Returns:
            List of commands for the step
        """
        if lab_id not in self.labs:
            return []
        
        lab = self.labs[lab_id]
        for step in lab.steps:
            if step.id == step_id:
                return step.cmds
        
        return []
    
    def get_step_hint(self, lab_id: str, step_id: str) -> Optional[str]:
        """
        Get hint/description for a specific step.
        
        Args:
            lab_id: Lab identifier
            step_id: Step identifier
            
        Returns:
            Step description or None
        """
        if lab_id not in self.labs:
            return None
        
        lab = self.labs[lab_id]
        for step in lab.steps:
            if step.id == step_id:
                return step.desc
        
        return None


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get or create the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
