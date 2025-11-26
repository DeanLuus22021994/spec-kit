-- Migration: V003 - Add advanced indexes for conversation queries
-- Description: Performance optimization for conversation and message queries
-- Author: System
-- Date: 2024

-- Composite index for user conversations ordered by recent activity
CREATE INDEX IF NOT EXISTS idx_conversations_user_recent
    ON conversations(user_id, created_at DESC)
    WHERE is_archived = FALSE;

-- Partial index for archived conversations
CREATE INDEX IF NOT EXISTS idx_conversations_archived
    ON conversations(user_id, updated_at DESC)
    WHERE is_archived = TRUE;

-- GIN index for conversation metadata JSONB queries
CREATE INDEX IF NOT EXISTS idx_conversations_metadata
    ON conversations USING gin (metadata);

-- GIN index for conversation context JSONB queries
CREATE INDEX IF NOT EXISTS idx_conversations_context
    ON conversations USING gin (context);

-- Composite index for message queries within conversation
CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
    ON messages(conversation_id, created_at DESC);

-- GIN index for message metadata
CREATE INDEX IF NOT EXISTS idx_messages_metadata
    ON messages USING gin (metadata);

-- Full-text search index on message content
CREATE INDEX IF NOT EXISTS idx_messages_content_fts
    ON messages USING gin (to_tsvector('english', content));

-- Function to search messages with full-text search
CREATE OR REPLACE FUNCTION search_messages(
    p_user_id UUID,
    p_search_query TEXT,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    message_id UUID,
    conversation_id UUID,
    conversation_title VARCHAR(255),
    role VARCHAR(20),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id as message_id,
        m.conversation_id,
        c.title as conversation_title,
        m.role,
        m.content,
        m.created_at,
        ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', p_search_query)) as rank
    FROM messages m
    INNER JOIN conversations c ON m.conversation_id = c.id
    WHERE c.user_id = p_user_id
      AND to_tsvector('english', m.content) @@ plainto_tsquery('english', p_search_query)
    ORDER BY rank DESC, m.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function to get conversation summary with message stats
CREATE OR REPLACE FUNCTION get_conversation_summary(
    p_conversation_id UUID
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    title VARCHAR(255),
    total_messages BIGINT,
    total_tokens BIGINT,
    first_message_at TIMESTAMP WITH TIME ZONE,
    last_message_at TIMESTAMP WITH TIME ZONE,
    models_used JSONB,
    is_archived BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.user_id,
        c.title,
        COUNT(m.id) as total_messages,
        SUM(COALESCE(m.tokens_used, 0)) as total_tokens,
        MIN(m.created_at) as first_message_at,
        MAX(m.created_at) as last_message_at,
        jsonb_agg(DISTINCT m.model) FILTER (WHERE m.model IS NOT NULL) as models_used,
        c.is_archived,
        c.created_at
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.id = p_conversation_id
    GROUP BY c.id, c.user_id, c.title, c.is_archived, c.created_at;
END;
$$ LANGUAGE plpgsql;

-- Index on planner executions for status queries
CREATE INDEX IF NOT EXISTS idx_planner_executions_status
    ON planner_executions(user_id, status, created_at DESC);

-- Index on function executions for performance monitoring
CREATE INDEX IF NOT EXISTS idx_function_executions_perf
    ON function_executions(function_name, created_at DESC, execution_time_ms);

-- Composite index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action
    ON audit_logs(user_id, action, created_at DESC);

-- GIN index for audit log changes JSONB
CREATE INDEX IF NOT EXISTS idx_audit_logs_changes
    ON audit_logs USING gin (changes);

-- Record migration
INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
VALUES ('003', 'Add advanced indexes for conversation and message queries', 0, md5('V003__conversation_indexes.sql'))
ON CONFLICT (version) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✓ Migration V003 completed: Advanced conversation indexes created';
    RAISE NOTICE '✓ Full-text search enabled on message content';
    RAISE NOTICE '✓ JSONB indexes created for metadata queries';
END $$;
