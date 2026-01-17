-- Initialize database with pgvector extension
-- This script runs automatically when the PostgreSQL container is first created

-- Create extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create a test table to verify pgvector works (optional, can be removed)
-- CREATE TABLE IF NOT EXISTS test_vectors (
--     id SERIAL PRIMARY KEY,
--     embedding vector(384)
-- );

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized successfully';
END $$;

