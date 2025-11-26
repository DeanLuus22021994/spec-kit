-- =====================================================
-- Semantic Kernel Application Database Initialization
-- =====================================================
-- PostgreSQL 16 initialization script with full schema
-- Includes: Tables, Indexes, Functions, Triggers, Views
-- =====================================================

-- Note: Database and user are created by Docker entrypoint via POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
-- This script runs after the database and user are created by the entrypoint

-- Ensure the user role exists (created by entrypoint, but explicitly check)
-- This prevents "role does not exist" errors during healthchecks
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
        CREATE ROLE "user" WITH LOGIN PASSWORD 'password';
    END IF;
END
$$;

-- Grant database access
GRANT ALL PRIVILEGES ON DATABASE semantic_kernel TO "user";

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- =====================================================
-- SCHEMA: Core Application Tables
-- =====================================================

-- Users table with enhanced security
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Roles table for RBAC
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User-Role junction table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, role_id)
);

-- Sessions table for authentication
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    token VARCHAR(512) NOT NULL UNIQUE,
    refresh_token VARCHAR(512),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SCHEMA: Semantic Kernel Specific Tables
-- =====================================================

-- Conversations/Chat history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255),
    context JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages within conversations
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'function')),
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Semantic memory/embeddings metadata
CREATE TABLE IF NOT EXISTS semantic_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    collection_name VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    description TEXT,
    additional_metadata JSONB DEFAULT '{}'::jsonb,
    embedding_id VARCHAR(255), -- Reference to Qdrant vector ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (collection_name, key)
);

-- Skills/Plugins registry
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),
    version VARCHAR(50),
    is_enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function execution logs
CREATE TABLE IF NOT EXISTS function_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id UUID REFERENCES skills(id) ON DELETE SET NULL,
    function_name VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    input_parameters JSONB,
    output_result JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(50) CHECK (status IN ('success', 'error', 'pending', 'cancelled')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Planner executions
CREATE TABLE IF NOT EXISTS planner_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    goal TEXT NOT NULL,
    plan JSONB NOT NULL, -- The generated plan steps
    status VARCHAR(50) CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    steps_completed INTEGER DEFAULT 0,
    total_steps INTEGER,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_is_archived ON conversations(is_archived);

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Semantic memories indexes
CREATE INDEX IF NOT EXISTS idx_semantic_memories_user_id ON semantic_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_collection ON semantic_memories(collection_name);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_key ON semantic_memories(key);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_text_trgm ON semantic_memories USING gin (text gin_trgm_ops);

-- Function executions indexes
CREATE INDEX IF NOT EXISTS idx_function_executions_user_id ON function_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_function_executions_created_at ON function_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_function_executions_status ON function_executions(status);

-- API usage indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at DESC);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type_id ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- =====================================================
-- FUNCTIONS: Triggers for updated_at
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_semantic_memories_updated_at BEFORE UPDATE ON semantic_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_planner_executions_updated_at BEFORE UPDATE ON planner_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- FUNCTIONS: Business Logic
-- =====================================================

-- Authenticate user and return user info with roles
CREATE OR REPLACE FUNCTION authenticate_user(
    p_username VARCHAR(50),
    p_password_hash VARCHAR(255)
)
RETURNS TABLE (
    user_id UUID,
    username VARCHAR(50),
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN,
    roles JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.username,
        u.email,
        u.first_name,
        u.last_name,
        u.is_active,
        COALESCE(jsonb_agg(jsonb_build_object('id', r.id, 'name', r.name, 'permissions', r.permissions))
            FILTER (WHERE r.id IS NOT NULL), '[]'::jsonb) as roles
    FROM users u
    LEFT JOIN user_roles ur ON u.id = ur.user_id
    LEFT JOIN roles r ON ur.role_id = r.id
    WHERE u.username = p_username
      AND u.password_hash = p_password_hash
      AND u.is_active = TRUE
    GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.is_active;

    -- Update last login
    UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE username = p_username;
END;
$$ LANGUAGE plpgsql;

-- Create session
CREATE OR REPLACE FUNCTION create_session(
    p_user_id UUID,
    p_token VARCHAR(512),
    p_refresh_token VARCHAR(512),
    p_expires_at TIMESTAMP WITH TIME ZONE,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    session_id UUID;
BEGIN
    INSERT INTO sessions (user_id, token, refresh_token, expires_at, ip_address, user_agent)
    VALUES (p_user_id, p_token, p_refresh_token, p_expires_at, p_ip_address, p_user_agent)
    RETURNING id INTO session_id;

    RETURN session_id;
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Get user conversation history
CREATE OR REPLACE FUNCTION get_user_conversations(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0,
    p_include_archived BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(255),
    message_count BIGINT,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.title,
        COUNT(m.id) as message_count,
        MAX(m.created_at) as last_message_at,
        c.created_at
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.user_id = p_user_id
      AND (c.is_archived = FALSE OR p_include_archived = TRUE)
    GROUP BY c.id, c.title, c.created_at
    ORDER BY MAX(m.created_at) DESC NULLS LAST
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Get API usage statistics
CREATE OR REPLACE FUNCTION get_api_usage_stats(
    p_user_id UUID,
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    total_requests BIGINT,
    total_tokens BIGINT,
    total_cost DECIMAL(10, 6),
    avg_response_time_ms DECIMAL(10, 2),
    requests_by_endpoint JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_requests,
        SUM(tokens_used) as total_tokens,
        SUM(cost_usd) as total_cost,
        AVG(response_time_ms)::DECIMAL(10, 2) as avg_response_time_ms,
        jsonb_object_agg(endpoint, request_count) as requests_by_endpoint
    FROM (
        SELECT
            endpoint,
            COUNT(*) as request_count,
            tokens_used,
            cost_usd,
            response_time_ms
        FROM api_usage
        WHERE user_id = p_user_id
          AND created_at BETWEEN p_start_date AND p_end_date
        GROUP BY endpoint, tokens_used, cost_usd, response_time_ms
    ) subquery;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS: Useful data aggregations
-- =====================================================

-- Active users with their roles
CREATE OR REPLACE VIEW v_active_users AS
SELECT
    u.id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.last_login_at,
    u.created_at,
    COALESCE(jsonb_agg(jsonb_build_object('name', r.name, 'permissions', r.permissions))
        FILTER (WHERE r.id IS NOT NULL), '[]'::jsonb) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.last_login_at, u.created_at;

-- Recent conversations with metadata
CREATE OR REPLACE VIEW v_recent_conversations AS
SELECT
    c.id,
    c.user_id,
    u.username,
    c.title,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_at,
    c.created_at,
    c.is_archived
FROM conversations c
INNER JOIN users u ON c.user_id = u.id
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.user_id, u.username, c.title, c.created_at, c.is_archived
ORDER BY MAX(m.created_at) DESC NULLS LAST;

-- =====================================================
-- SEED DATA: Default Roles and Admin User
-- =====================================================

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
    ('admin', 'Administrator with full system access',
     '["*"]'::jsonb),
    ('user', 'Standard user with basic access',
     '["read:own", "write:own", "execute:skills"]'::jsonb),
    ('developer', 'Developer with extended permissions',
     '["read:*", "write:own", "execute:skills", "manage:skills"]'::jsonb),
    ('readonly', 'Read-only access for viewing',
     '["read:*"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Insert default admin user (password: Admin@123 - CHANGE IN PRODUCTION!)
-- Password hash generated with bcrypt cost factor 12
INSERT INTO users (username, email, password_hash, first_name, last_name, is_verified) VALUES
    ('admin', 'admin@semantic-kernel.local',
     '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIiIr5LfSa',
     'System', 'Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Assign admin role to admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Insert default skills
INSERT INTO skills (name, description, category, version, configuration) VALUES
    ('TextSummarization', 'Summarize long text into concise summaries', 'NLP', '1.0.0',
     '{"max_length": 500, "model": "gpt-4"}'::jsonb),
    ('CodeGeneration', 'Generate code based on natural language descriptions', 'Development', '1.0.0',
     '{"languages": ["python", "javascript", "csharp"], "model": "gpt-4"}'::jsonb),
    ('DataAnalysis', 'Analyze and visualize data', 'Analytics', '1.0.0',
     '{"supported_formats": ["csv", "json", "excel"]}'::jsonb),
    ('WebSearch', 'Search the web for information', 'Search', '1.0.0',
     '{"max_results": 10, "safe_search": true}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '✓ Semantic Kernel database initialization completed successfully';
    RAISE NOTICE '✓ Created % tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE');
    RAISE NOTICE '✓ Created % indexes', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE '✓ Created % functions', (SELECT COUNT(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public' AND p.prokind = 'f');
    RAISE NOTICE '✓ Created % views', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public');
    RAISE NOTICE '⚠ Default admin credentials: username=admin, password=Admin@123';
    RAISE NOTICE '⚠ CHANGE DEFAULT PASSWORD IN PRODUCTION!';
END $$;
