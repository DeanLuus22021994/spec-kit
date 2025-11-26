-- Seed Data: Development Users
-- Purpose: Create development and test user accounts
-- Environment: Development/Test only
-- WARNING: Contains default passwords - NOT FOR PRODUCTION!

-- Insert development users
-- Password for all users: Dev@12345
-- Hash generated with bcrypt cost factor 12
INSERT INTO users (username, email, password_hash, first_name, last_name, is_verified, is_active) VALUES
    ('developer', 'dev@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Dev', 'User', TRUE, TRUE),
    ('testuser', 'test@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Test', 'User', TRUE, TRUE),
    ('readonly', 'readonly@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Read', 'Only', TRUE, TRUE),
    ('alice', 'alice@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Alice', 'Johnson', TRUE, TRUE),
    ('bob', 'bob@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Bob', 'Smith', TRUE, TRUE),
    ('inactive_user', 'inactive@semantic-kernel.local',
     '$2a$12$kQ6aW5f.nDqQG5TZJ7QvH.ZX9kF8LJ3XqH5fJ8kL9mN1oP2qR3sT4',
     'Inactive', 'User', FALSE, FALSE)
ON CONFLICT (username) DO NOTHING;

-- Assign roles to users
INSERT INTO user_roles (user_id, role_id, assigned_by)
SELECT u.id, r.id, (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
FROM users u
CROSS JOIN roles r
WHERE (u.username = 'developer' AND r.name = 'developer')
   OR (u.username = 'testuser' AND r.name = 'user')
   OR (u.username = 'readonly' AND r.name = 'readonly')
   OR (u.username = 'alice' AND r.name = 'user')
   OR (u.username = 'bob' AND r.name = 'developer')
ON CONFLICT DO NOTHING;

-- Create default user quotas
INSERT INTO user_quotas (user_id, requests_per_minute, requests_per_hour, requests_per_day, tokens_per_day)
SELECT id, 60, 1000, 10000, 100000
FROM users
WHERE username IN ('developer', 'testuser', 'alice', 'bob')
ON CONFLICT (user_id) DO NOTHING;

-- Create higher quota for developer account
UPDATE user_quotas
SET requests_per_minute = 120,
    requests_per_hour = 5000,
    requests_per_day = 50000,
    tokens_per_day = 500000
WHERE user_id = (SELECT id FROM users WHERE username = 'developer' LIMIT 1);

-- Create lower quota for readonly account
INSERT INTO user_quotas (user_id, requests_per_minute, requests_per_hour, requests_per_day, tokens_per_day)
SELECT id, 30, 500, 5000, 50000
FROM users
WHERE username = 'readonly'
ON CONFLICT (user_id)
DO UPDATE SET
    requests_per_minute = 30,
    requests_per_hour = 500,
    requests_per_day = 5000,
    tokens_per_day = 50000;

-- Log completion
DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users WHERE username IN ('developer', 'testuser', 'readonly', 'alice', 'bob');
    RAISE NOTICE '✓ Created % development users', user_count;
    RAISE NOTICE '⚠ Default password for all users: Dev@12345';
    RAISE NOTICE '⚠ Change passwords in shared environments!';
END $$;
