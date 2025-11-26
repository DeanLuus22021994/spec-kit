-- Migration: V002 - Install pgvector extension
-- Description: Enables vector similarity search for semantic embeddings
-- Author: System
-- Date: 2024

-- Install pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table with vector column
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    collection_name VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimensions
    model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_collection
    ON embeddings(collection_name);

CREATE INDEX IF NOT EXISTS idx_embeddings_user_id
    ON embeddings(user_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_content_hash
    ON embeddings(content_hash);

-- Create vector similarity index (IVFFlat for faster approximate search)
-- Adjust lists parameter based on dataset size: sqrt(total_rows) is a good starting point
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Alternative: HNSW index for even faster searches (requires more memory)
-- CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw
--     ON embeddings USING hnsw (embedding vector_cosine_ops);

-- Function to search similar embeddings
CREATE OR REPLACE FUNCTION search_similar_embeddings(
    query_embedding vector(1536),
    p_collection VARCHAR(255),
    p_user_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    text TEXT,
    metadata JSONB,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.text,
        e.metadata,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings e
    WHERE e.collection_name = p_collection
      AND (p_user_id IS NULL OR e.user_id = p_user_id)
      AND 1 - (e.embedding <=> query_embedding) >= p_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to find nearest neighbors with metadata filtering
CREATE OR REPLACE FUNCTION search_embeddings_with_filter(
    query_embedding vector(1536),
    p_collection VARCHAR(255),
    p_metadata_filter JSONB DEFAULT '{}'::jsonb,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    text TEXT,
    metadata JSONB,
    distance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.text,
        e.metadata,
        e.embedding <=> query_embedding as distance
    FROM embeddings e
    WHERE e.collection_name = p_collection
      AND (p_metadata_filter = '{}'::jsonb OR e.metadata @> p_metadata_filter)
    ORDER BY e.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_embeddings_updated_at
    BEFORE UPDATE ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Record migration
INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
VALUES ('002', 'Install pgvector extension and create embeddings table', 0, md5('V002__pgvector_extension.sql'))
ON CONFLICT (version) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✓ Migration V002 completed: pgvector extension installed';
    RAISE NOTICE '✓ Created embeddings table with vector(1536) column';
    RAISE NOTICE '✓ Created similarity search functions';
END $$;
