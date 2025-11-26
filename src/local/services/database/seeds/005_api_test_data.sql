-- Seed Data: API Usage Test Data
-- Purpose: Create sample API usage data for testing analytics and monitoring
-- Environment: Development/Test only

DO $$
DECLARE
    v_alice_id UUID;
    v_bob_id UUID;
    v_dev_id UUID;
    i INTEGER;
    random_endpoint TEXT;
    random_status INTEGER;
    random_tokens INTEGER;
BEGIN
    SELECT id INTO v_alice_id FROM users WHERE username = 'alice' LIMIT 1;
    SELECT id INTO v_bob_id FROM users WHERE username = 'bob' LIMIT 1;
    SELECT id INTO v_dev_id FROM users WHERE username = 'developer' LIMIT 1;

    -- Generate API usage data for the last 7 days
    FOR i IN 1..100 LOOP
        -- Random endpoint
        random_endpoint := (ARRAY[
            '/api/conversations',
            '/api/messages',
            '/api/skills/execute',
            '/api/embeddings/search',
            '/api/users/profile',
            '/api/planner/create',
            '/api/auth/login',
            '/api/health'
        ])[1 + floor(random() * 8)::int];

        -- Random status code (mostly successful)
        random_status := CASE
            WHEN random() < 0.90 THEN 200
            WHEN random() < 0.95 THEN 201
            WHEN random() < 0.97 THEN 400
            WHEN random() < 0.99 THEN 404
            ELSE 500
        END;

        -- Random token usage (0 for non-AI endpoints)
        random_tokens := CASE
            WHEN random_endpoint LIKE '%skills%' OR random_endpoint LIKE '%embeddings%' THEN
                floor(random() * 2000 + 100)::int
            ELSE 0
        END;

        -- Insert API usage record for Alice
        INSERT INTO api_usage (user_id, endpoint, method, status_code, response_time_ms, tokens_used, cost_usd, created_at)
        VALUES (
            v_alice_id,
            random_endpoint,
            CASE WHEN random_endpoint LIKE '%auth%' THEN 'POST'
                 WHEN random() < 0.7 THEN 'GET'
                 ELSE 'POST' END,
            random_status,
            floor(random() * 500 + 50)::int,
            random_tokens,
            CASE WHEN random_tokens > 0 THEN (random_tokens * 0.0001)::decimal(10,6) ELSE 0 END,
            CURRENT_TIMESTAMP - (random() * INTERVAL '7 days')
        );

        -- 30% chance to add record for Bob
        IF random() < 0.3 THEN
            INSERT INTO api_usage (user_id, endpoint, method, status_code, response_time_ms, tokens_used, cost_usd, created_at)
            VALUES (
                v_bob_id,
                random_endpoint,
                'GET',
                random_status,
                floor(random() * 400 + 30)::int,
                random_tokens,
                CASE WHEN random_tokens > 0 THEN (random_tokens * 0.0001)::decimal(10,6) ELSE 0 END,
                CURRENT_TIMESTAMP - (random() * INTERVAL '7 days')
            );
        END IF;

        -- 20% chance to add record for Developer
        IF random() < 0.2 THEN
            INSERT INTO api_usage (user_id, endpoint, method, status_code, response_time_ms, tokens_used, cost_usd, created_at)
            VALUES (
                v_dev_id,
                random_endpoint,
                CASE WHEN random() < 0.5 THEN 'GET' ELSE 'POST' END,
                random_status,
                floor(random() * 300 + 20)::int,
                random_tokens,
                CASE WHEN random_tokens > 0 THEN (random_tokens * 0.0001)::decimal(10,6) ELSE 0 END,
                CURRENT_TIMESTAMP - (random() * INTERVAL '7 days')
            );
        END IF;
    END LOOP;

    -- Create some audit log entries
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at)
    VALUES
        (v_alice_id, 'CREATE_CONVERSATION', 'conversation',
         (SELECT id FROM conversations WHERE user_id = v_alice_id LIMIT 1),
         '{"title": "New conversation created"}'::jsonb,
         '192.168.1.100'::inet,
         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         CURRENT_TIMESTAMP - INTERVAL '3 days'),
        (v_alice_id, 'UPDATE_PROFILE', 'user', v_alice_id,
         '{"fields_changed": ["email", "last_name"], "old_email": "alice@old.com", "new_email": "alice@semantic-kernel.local"}'::jsonb,
         '192.168.1.100'::inet,
         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         CURRENT_TIMESTAMP - INTERVAL '5 days'),
        (v_bob_id, 'EXECUTE_SKILL', 'skill',
         (SELECT id FROM skills WHERE name = 'CodeGeneration' LIMIT 1),
         '{"function": "GenerateCode", "status": "success"}'::jsonb,
         '192.168.1.101'::inet,
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
         CURRENT_TIMESTAMP - INTERVAL '1 day'),
        (v_dev_id, 'DELETE_SESSION', 'session', uuid_generate_v4(),
         '{"reason": "user_logout", "duration_minutes": 45}'::jsonb,
         '192.168.1.102'::inet,
         'Mozilla/5.0 (X11; Linux x86_64)',
         CURRENT_TIMESTAMP - INTERVAL '2 hours');

    -- Create some rate limit tracking data
    INSERT INTO rate_limit_tracking (user_id, window_start, window_type, request_count, token_count)
    VALUES
        (v_alice_id, date_trunc('hour', CURRENT_TIMESTAMP), 'hour', 45, 8500),
        (v_alice_id, date_trunc('day', CURRENT_TIMESTAMP), 'day', 230, 42000),
        (v_bob_id, date_trunc('hour', CURRENT_TIMESTAMP), 'hour', 28, 3200),
        (v_bob_id, date_trunc('day', CURRENT_TIMESTAMP), 'day', 156, 18500),
        (v_dev_id, date_trunc('hour', CURRENT_TIMESTAMP), 'hour', 89, 15000),
        (v_dev_id, date_trunc('day', CURRENT_TIMESTAMP), 'day', 445, 75000);

    RAISE NOTICE '✓ Created % API usage records', (SELECT COUNT(*) FROM api_usage);
    RAISE NOTICE '✓ Created % audit log entries', (SELECT COUNT(*) FROM audit_logs);
    RAISE NOTICE '✓ Created rate limit tracking data';
    RAISE NOTICE '✓ Test data spans last 7 days';
END $$;
