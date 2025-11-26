-- Migration: V004 - API Rate Limiting Tables
-- Description: Add tables and functions for API rate limiting and quotas
-- Author: System
-- Date: 2024

-- User quotas table
CREATE TABLE IF NOT EXISTS user_quotas (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    requests_per_minute INTEGER DEFAULT 60,
    requests_per_hour INTEGER DEFAULT 1000,
    requests_per_day INTEGER DEFAULT 10000,
    tokens_per_day INTEGER DEFAULT 100000,
    max_concurrent_requests INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rate limit tracking table (uses time-series approach)
CREATE TABLE IF NOT EXISTS rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_type VARCHAR(10) CHECK (window_type IN ('minute', 'hour', 'day')),
    request_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, window_start, window_type)
);

-- Index for rate limit lookups
CREATE INDEX IF NOT EXISTS idx_rate_limit_tracking_window
    ON rate_limit_tracking(user_id, window_type, window_start DESC);

-- Auto-cleanup old rate limit data (keep last 7 days)
CREATE INDEX IF NOT EXISTS idx_rate_limit_tracking_cleanup
    ON rate_limit_tracking(window_start)
    WHERE window_start < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Function to check rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_user_id UUID,
    p_tokens INTEGER DEFAULT 0
)
RETURNS TABLE (
    allowed BOOLEAN,
    limit_type VARCHAR(20),
    current_count INTEGER,
    max_count INTEGER,
    reset_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    v_quotas user_quotas;
    v_minute_count INTEGER;
    v_hour_count INTEGER;
    v_day_count INTEGER;
    v_day_tokens INTEGER;
    v_minute_start TIMESTAMP WITH TIME ZONE;
    v_hour_start TIMESTAMP WITH TIME ZONE;
    v_day_start TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get user quotas (or defaults)
    SELECT * INTO v_quotas FROM user_quotas WHERE user_id = p_user_id;

    IF v_quotas IS NULL THEN
        -- Create default quota
        INSERT INTO user_quotas (user_id) VALUES (p_user_id)
        RETURNING * INTO v_quotas;
    END IF;

    -- Calculate window starts
    v_minute_start := date_trunc('minute', CURRENT_TIMESTAMP);
    v_hour_start := date_trunc('hour', CURRENT_TIMESTAMP);
    v_day_start := date_trunc('day', CURRENT_TIMESTAMP);

    -- Get current counts
    SELECT COALESCE(request_count, 0) INTO v_minute_count
    FROM rate_limit_tracking
    WHERE user_id = p_user_id
      AND window_type = 'minute'
      AND window_start = v_minute_start;

    SELECT COALESCE(request_count, 0) INTO v_hour_count
    FROM rate_limit_tracking
    WHERE user_id = p_user_id
      AND window_type = 'hour'
      AND window_start = v_hour_start;

    SELECT COALESCE(request_count, 0), COALESCE(token_count, 0)
    INTO v_day_count, v_day_tokens
    FROM rate_limit_tracking
    WHERE user_id = p_user_id
      AND window_type = 'day'
      AND window_start = v_day_start;

    -- Check limits
    IF v_minute_count >= v_quotas.requests_per_minute THEN
        RETURN QUERY SELECT FALSE, 'requests_per_minute'::VARCHAR(20), v_minute_count,
            v_quotas.requests_per_minute, v_minute_start + INTERVAL '1 minute';
        RETURN;
    END IF;

    IF v_hour_count >= v_quotas.requests_per_hour THEN
        RETURN QUERY SELECT FALSE, 'requests_per_hour'::VARCHAR(20), v_hour_count,
            v_quotas.requests_per_hour, v_hour_start + INTERVAL '1 hour';
        RETURN;
    END IF;

    IF v_day_count >= v_quotas.requests_per_day THEN
        RETURN QUERY SELECT FALSE, 'requests_per_day'::VARCHAR(20), v_day_count,
            v_quotas.requests_per_day, v_day_start + INTERVAL '1 day';
        RETURN;
    END IF;

    IF v_day_tokens + p_tokens > v_quotas.tokens_per_day THEN
        RETURN QUERY SELECT FALSE, 'tokens_per_day'::VARCHAR(20), v_day_tokens,
            v_quotas.tokens_per_day, v_day_start + INTERVAL '1 day';
        RETURN;
    END IF;

    -- All checks passed
    RETURN QUERY SELECT TRUE, NULL::VARCHAR(20), 0, 0, NULL::TIMESTAMP WITH TIME ZONE;
END;
$$ LANGUAGE plpgsql;

-- Function to increment rate limit counters
CREATE OR REPLACE FUNCTION increment_rate_limit(
    p_user_id UUID,
    p_tokens INTEGER DEFAULT 0
)
RETURNS VOID AS $$
DECLARE
    v_minute_start TIMESTAMP WITH TIME ZONE;
    v_hour_start TIMESTAMP WITH TIME ZONE;
    v_day_start TIMESTAMP WITH TIME ZONE;
BEGIN
    v_minute_start := date_trunc('minute', CURRENT_TIMESTAMP);
    v_hour_start := date_trunc('hour', CURRENT_TIMESTAMP);
    v_day_start := date_trunc('day', CURRENT_TIMESTAMP);

    -- Increment minute counter
    INSERT INTO rate_limit_tracking (user_id, window_start, window_type, request_count)
    VALUES (p_user_id, v_minute_start, 'minute', 1)
    ON CONFLICT (user_id, window_start, window_type)
    DO UPDATE SET request_count = rate_limit_tracking.request_count + 1;

    -- Increment hour counter
    INSERT INTO rate_limit_tracking (user_id, window_start, window_type, request_count)
    VALUES (p_user_id, v_hour_start, 'hour', 1)
    ON CONFLICT (user_id, window_start, window_type)
    DO UPDATE SET request_count = rate_limit_tracking.request_count + 1;

    -- Increment day counter and token count
    INSERT INTO rate_limit_tracking (user_id, window_start, window_type, request_count, token_count)
    VALUES (p_user_id, v_day_start, 'day', 1, p_tokens)
    ON CONFLICT (user_id, window_start, window_type)
    DO UPDATE SET
        request_count = rate_limit_tracking.request_count + 1,
        token_count = rate_limit_tracking.token_count + p_tokens;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old rate limit data
CREATE OR REPLACE FUNCTION cleanup_rate_limit_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rate_limit_tracking
    WHERE window_start < CURRENT_TIMESTAMP - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_quotas updated_at
CREATE TRIGGER update_user_quotas_updated_at
    BEFORE UPDATE ON user_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Record migration
INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
VALUES ('004', 'Add API rate limiting tables and functions', 0, md5('V004__api_rate_limiting.sql'))
ON CONFLICT (version) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✓ Migration V004 completed: Rate limiting tables created';
    RAISE NOTICE '✓ Default quotas: 60/min, 1000/hour, 10000/day requests';
    RAISE NOTICE '✓ Token quota: 100000/day';
END $$;
