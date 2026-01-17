"""
BERT Embeddings and TF-IDF Vectorizer for semantic similarity
"""
import logging
import numpy as np
from typing import List, Optional, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using BERT and TF-IDF"""
    
    def __init__(self):
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.bert_model: Optional[SentenceTransformer] = None
        self.use_gpu = torch.cuda.is_available()
        
        # Initialize TF-IDF
        self._init_tfidf()
        
        # Initialize BERT (lazy loading)
        self._bert_loaded = False
    
    def _init_tfidf(self) -> None:
        """Initialize TF-IDF vectorizer"""
        try:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english',
                min_df=2,
                max_df=0.95
            )
            logger.info("TF-IDF vectorizer initialized")
        except Exception as e:
            logger.error(f"Error initializing TF-IDF: {str(e)}")
    
    def _load_bert_model(self) -> None:
        """Lazy load BERT model"""
        if self._bert_loaded:
            return
        
        try:
            model_name = "all-MiniLM-L6-v2"  # Lightweight and fast
            self.bert_model = SentenceTransformer(model_name)
            
            if self.use_gpu:
                self.bert_model = self.bert_model.to('cuda')
                logger.info("BERT model loaded on GPU")
            else:
                logger.info("BERT model loaded on CPU")
            
            self._bert_loaded = True
        except Exception as e:
            logger.error(f"Error loading BERT model: {str(e)}")
            self.bert_model = None
    
    def generate_tfidf_embedding(self, text: str, fit: bool = False) -> Optional[np.ndarray]:
        """
        Generate TF-IDF embedding for text
        
        Args:
            text: Input text
            fit: Whether to fit the vectorizer (for first use)
            
        Returns:
            TF-IDF embedding vector
        """
        if not self.tfidf_vectorizer:
            return None
        
        try:
            if fit:
                self.tfidf_vectorizer.fit([text])
            
            embedding = self.tfidf_vectorizer.transform([text])
            return embedding.toarray()[0]
        except Exception as e:
            logger.error(f"Error generating TF-IDF embedding: {str(e)}")
            return None
    
    def generate_bert_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate BERT embedding for text
        
        Args:
            text: Input text
            
        Returns:
            BERT embedding vector (384 dimensions for all-MiniLM-L6-v2)
        """
        self._load_bert_model()
        
        if not self.bert_model:
            return None
        
        try:
            embedding = self.bert_model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating BERT embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        method: str = "bert"
    ) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of input texts
            method: 'bert' or 'tfidf'
            
        Returns:
            List of embedding vectors
        """
        if method == "bert":
            self._load_bert_model()
            if not self.bert_model:
                return [None] * len(texts)
            
            try:
                embeddings = self.bert_model.encode(
                    texts,
                    convert_to_numpy=True,
                    show_progress_bar=True,
                    batch_size=32
                )
                return [emb for emb in embeddings]
            except Exception as e:
                logger.error(f"Error generating batch BERT embeddings: {str(e)}")
                return [None] * len(texts)
        
        elif method == "tfidf":
            if not self.tfidf_vectorizer:
                return [None] * len(texts)
            
            try:
                # Fit on all texts if not already fitted
                if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                    self.tfidf_vectorizer.fit(texts)
                
                embeddings = self.tfidf_vectorizer.transform(texts)
                return [emb.toarray()[0] for emb in embeddings]
            except Exception as e:
                logger.error(f"Error generating batch TF-IDF embeddings: {str(e)}")
                return [None] * len(texts)
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        method: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            method: 'cosine' or 'euclidean'
            
        Returns:
            Similarity score (0-1 for cosine, distance for euclidean)
        """
        try:
            if method == "cosine":
                # Cosine similarity
                dot_product = np.dot(embedding1, embedding2)
                norm1 = np.linalg.norm(embedding1)
                norm2 = np.linalg.norm(embedding2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                similarity = dot_product / (norm1 * norm2)
                return float(similarity)
            
            elif method == "euclidean":
                # Euclidean distance (convert to similarity)
                distance = np.linalg.norm(embedding1 - embedding2)
                # Normalize to 0-1 range (assuming max distance of 2 for normalized vectors)
                similarity = 1.0 / (1.0 + distance)
                return float(similarity)
            
            else:
                raise ValueError(f"Unknown similarity method: {method}")
        
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0


# Singleton instance
embedding_generator = EmbeddingGenerator()

