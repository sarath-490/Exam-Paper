"""
FAISS-based embedding service for semantic question similarity
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Tuple, Optional
import pickle
import os
from app.core.config import settings


class EmbeddingService:
    """Service for creating and searching question embeddings using FAISS"""
    
    def __init__(self):
        """Initialize the embedding model and FAISS index"""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension of all-MiniLM-L6-v2 embeddings
        self.index = faiss.IndexFlatL2(self.dimension)
        self.question_ids = []  # Store question IDs corresponding to embeddings
        self.index_file = "faiss_index.bin"
        self.ids_file = "question_ids.pkl"
        
        # Load existing index if available
        self._load_index()
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text"""
        return self.model.encode([text])[0]
    
    def create_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for multiple texts"""
        return self.model.encode(texts)
    
    def add_question(self, question_text: str, question_id: str):
        """Add a question to the FAISS index"""
        embedding = self.create_embedding(question_text)
        self.index.add(np.array([embedding]))
        self.question_ids.append(question_id)
        self._save_index()
    
    def add_questions_batch(self, questions: List[Tuple[str, str]]):
        """Add multiple questions to the FAISS index
        
        Args:
            questions: List of (question_text, question_id) tuples
        """
        if not questions:
            return
        
        texts = [q[0] for q in questions]
        ids = [q[1] for q in questions]
        
        embeddings = self.create_embeddings_batch(texts)
        self.index.add(embeddings)
        self.question_ids.extend(ids)
        self._save_index()
    
    def check_similarity(
        self, 
        question_text: str, 
        threshold: float = 0.90,
        k: int = 5
    ) -> Tuple[bool, List[Tuple[str, float]]]:
        """Check if a similar question exists
        
        Args:
            question_text: The question to check
            threshold: Similarity threshold (0-1, higher = more similar)
            k: Number of nearest neighbors to check
        
        Returns:
            (is_similar, [(question_id, similarity_score), ...])
        """
        if self.index.ntotal == 0:
            return False, []
        
        embedding = self.create_embedding(question_text)
        
        # Search for k nearest neighbors
        D, I = self.index.search(np.array([embedding]), min(k, self.index.ntotal))
        
        # Convert distances to similarity scores (0-1)
        # L2 distance: lower is more similar
        # Convert to similarity: 1 / (1 + distance)
        similarities = []
        for dist, idx in zip(D[0], I[0]):
            if idx != -1 and idx < len(self.question_ids):
                similarity = 1 / (1 + dist)
                similarities.append((self.question_ids[idx], similarity))
        
        # Check if any similarity exceeds threshold
        is_similar = any(sim >= threshold for _, sim in similarities)
        
        return is_similar, similarities
    
    def find_similar_questions(
        self, 
        question_text: str, 
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """Find k most similar questions
        
        Returns:
            List of (question_id, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        embedding = self.create_embedding(question_text)
        D, I = self.index.search(np.array([embedding]), min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx != -1 and idx < len(self.question_ids):
                similarity = 1 / (1 + dist)
                results.append((self.question_ids[idx], similarity))
        
        return results
    
    def remove_question(self, question_id: str):
        """Remove a question from the index
        
        Note: FAISS doesn't support direct deletion, so we rebuild the index
        """
        if question_id not in self.question_ids:
            return
        
        # Get index of question to remove
        idx = self.question_ids.index(question_id)
        
        # Remove from question_ids
        self.question_ids.pop(idx)
        
        # Rebuild index without this question
        # This is inefficient but necessary with FAISS
        self._rebuild_index()
    
    def get_index_stats(self) -> dict:
        """Get statistics about the FAISS index"""
        return {
            "total_questions": self.index.ntotal,
            "dimension": self.dimension,
            "index_size_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024)
        }
    
    def _save_index(self):
        """Save FAISS index and question IDs to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_file)
            
            # Save question IDs
            with open(self.ids_file, 'wb') as f:
                pickle.dump(self.question_ids, f)
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
    
    def _load_index(self):
        """Load FAISS index and question IDs from disk"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.ids_file):
                # Load FAISS index
                self.index = faiss.read_index(self.index_file)
                
                # Load question IDs
                with open(self.ids_file, 'rb') as f:
                    self.question_ids = pickle.load(f)
                
                print(f"✅ Loaded FAISS index with {self.index.ntotal} questions")
        except Exception as e:
            print(f"⚠️  Could not load FAISS index: {e}")
            # Initialize new index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.question_ids = []
    
    def _rebuild_index(self):
        """Rebuild the entire FAISS index (used after deletion)"""
        # This is a placeholder - in production, you'd fetch all questions
        # from database and rebuild
        self.index = faiss.IndexFlatL2(self.dimension)
        self._save_index()
    
    def clear_index(self):
        """Clear the entire FAISS index"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.question_ids = []
        self._save_index()
    
    async def delete_embeddings_by_resource(self, resource_id: str) -> int:
        """Delete all embeddings associated with a resource
        
        Args:
            resource_id: The resource ID to delete embeddings for
            
        Returns:
            Number of embeddings deleted
        """
        # Filter out question IDs that belong to this resource
        # Question IDs are typically stored as "resource_id:question_index" or similar
        original_count = len(self.question_ids)
        
        # Remove question IDs that start with the resource_id
        self.question_ids = [
            qid for qid in self.question_ids 
            if not qid.startswith(f"{resource_id}:")
        ]
        
        deleted_count = original_count - len(self.question_ids)
        
        if deleted_count > 0:
            # Rebuild index without the deleted embeddings
            self._rebuild_index()
            print(f"   Removed {deleted_count} embeddings for resource {resource_id}")
        
        return deleted_count


# Global instance
embedding_service = EmbeddingService()
