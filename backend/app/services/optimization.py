"""
Performance Optimization Service
FAISS for vector similarity, Redis caching, batch processing
"""
import logging
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
import faiss
import pickle
from app.core.redis_client import get_redis_client, cache_get, cache_set
from app.ml.embeddings import embedding_generator
import hashlib
import json

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Optimize performance with FAISS and caching"""
    
    def __init__(self):
        self.faiss_index: Optional[faiss.Index] = None
        self.embedding_dim = 384  # BERT embedding dimension
        self.cache_ttl = 3600  # 1 hour cache TTL
    
    def build_faiss_index(
        self,
        embeddings: List[np.ndarray],
        ids: Optional[List[str]] = None
    ) -> faiss.Index:
        """
        Build FAISS index for fast similarity search
        
        Args:
            embeddings: List of embedding vectors
            ids: Optional list of IDs for each embedding
            
        Returns:
            FAISS index
        """
        try:
            if not embeddings:
                raise ValueError("No embeddings provided")
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Create index (IVF for large datasets, Flat for small)
            if len(embeddings) > 1000:
                # Use IVF for large datasets
                quantizer = faiss.IndexFlatL2(self.embedding_dim)
                nlist = min(100, len(embeddings) // 10)  # Number of clusters
                index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
                index.train(embeddings_array)
                index.add(embeddings_array)
            else:
                # Use Flat index for small datasets
                index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine
                index.add(embeddings_array)
            
            self.faiss_index = index
            logger.info(f"Built FAISS index with {len(embeddings)} vectors")
            
            return index
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}", exc_info=True)
            raise
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors using FAISS
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (index, similarity_score) tuples
        """
        if self.faiss_index is None:
            raise ValueError("FAISS index not built. Call build_faiss_index first.")
        
        try:
            # Normalize query
            query = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query)
            
            # Search
            distances, indices = self.faiss_index.search(query, k)
            
            # Convert distances to similarities (for cosine: similarity = 1 - distance/2)
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx >= 0:  # Valid index
                    similarity = 1.0 - (dist / 2.0)  # Convert distance to similarity
                    if similarity >= threshold:
                        results.append((int(idx), float(similarity)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in FAISS search: {str(e)}", exc_info=True)
            return []
    
    def cache_embedding(
        self,
        key: str,
        embedding: np.ndarray
    ) -> bool:
        """Cache embedding in Redis"""
        try:
            redis_client = get_redis_client()
            embedding_bytes = pickle.dumps(embedding.tolist())
            redis_client.setex(
                f"embedding:{key}",
                self.cache_ttl,
                embedding_bytes
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {str(e)}")
            return False
    
    def get_cached_embedding(
        self,
        key: str
    ) -> Optional[np.ndarray]:
        """Get cached embedding from Redis"""
        try:
            redis_client = get_redis_client()
            cached = redis_client.get(f"embedding:{key}")
            if cached:
                embedding_list = pickle.loads(cached)
                return np.array(embedding_list)
        except Exception as e:
            logger.warning(f"Failed to get cached embedding: {str(e)}")
        return None
    
    def cache_match_result(
        self,
        job_id: str,
        candidate_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Cache match result"""
        try:
            redis_client = get_redis_client()
            cache_key = f"match:{job_id}:{candidate_id}"
            result_json = json.dumps(result)
            redis_client.setex(cache_key, self.cache_ttl, result_json)
            return True
        except Exception as e:
            logger.warning(f"Failed to cache match result: {str(e)}")
            return False
    
    def get_cached_match_result(
        self,
        job_id: str,
        candidate_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached match result"""
        try:
            redis_client = get_redis_client()
            cache_key = f"match:{job_id}:{candidate_id}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get cached match result: {str(e)}")
        return None
    
    def batch_process_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[Optional[np.ndarray]]:
        """Process embeddings in batch with caching"""
        embeddings = []
        
        for text in texts:
            # Generate cache key
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_key = f"text_embedding:{text_hash}"
            
            # Try cache first
            if use_cache:
                cached = self.get_cached_embedding(cache_key)
                if cached is not None:
                    embeddings.append(cached)
                    continue
            
            # Generate embedding
            embedding = embedding_generator.generate_bert_embedding(text)
            if embedding is not None:
                embeddings.append(embedding)
                # Cache it
                if use_cache:
                    self.cache_embedding(cache_key, embedding)
            else:
                embeddings.append(None)
        
        return embeddings
    
    def optimize_database_query(
        self,
        query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize database query parameters"""
        optimized = query_params.copy()
        
        # Add pagination if not present
        if 'limit' not in optimized:
            optimized['limit'] = 100  # Default limit
        
        # Add ordering
        if 'order_by' not in optimized:
            optimized['order_by'] = 'created_at'
            optimized['order_desc'] = True
        
        # Add index hints
        optimized['use_index'] = True
        
        return optimized


# Singleton instance
performance_optimizer = PerformanceOptimizer()

