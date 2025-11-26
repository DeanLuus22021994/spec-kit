-- NOTE: This seed file uses PostgreSQL syntax (pg-specific functions and jsonb casts).
-- If VS Code shows SQL diagnostics, install the 'PostgreSQL' extension and set the file language to PostgreSQL.

-- Insert conversations for Alice
INSERT INTO conversations (id, user_id, title, context, metadata)
SELECT uuid_generate_v4(), (SELECT id FROM users WHERE username = 'alice' LIMIT 1),
       title, context::jsonb, metadata::jsonb
FROM (VALUES
  ('Getting Started with Semantic Kernel', '{"max_tokens": 2000, "temperature": 0.7, "model": "gpt-4"}', '{"tags": ["tutorial", "introduction"], "language": "en"}'),
  ('Code Review: Authentication Service', '{"max_tokens": 4000, "temperature": 0.3, "model": "gpt-4"}', '{"tags": ["code-review", "security"], "language": "en"}'),
  ('Data Analysis: Sales Trends', '{"max_tokens": 3000, "temperature": 0.5, "model": "gpt-4"}', '{"tags": ["analytics", "business"], "language": "en"}')
) AS t(title, context, metadata)
ON CONFLICT (user_id, title) DO NOTHING;

-- Insert messages for Alice's first conversation
INSERT INTO messages (conversation_id, role, content, tokens_used, model, metadata)
VALUES
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Getting Started with Semantic Kernel' LIMIT 1),
    'user', 'What is Semantic Kernel and how can I get started?', 15, 'gpt-4', '{"timestamp": "2024-01-15T10:00:00Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Getting Started with Semantic Kernel' LIMIT 1),
    'assistant', 'Semantic Kernel is an open-source SDK that lets you easily build AI agents that can call your existing code. Here are the key concepts:\n\n1. **Skills**: Capabilities that your AI can use\n2. **Planners**: Automatically chain skills together\n3. **Memory**: Give your AI context and recall\n\nTo get started:\n```csharp\nvar kernel = Kernel.Builder.Build();\nkernel.ImportSkill(new TextSkill());\nvar result = await kernel.RunAsync("Summarize this text...");\n```',
    280, 'gpt-4', '{"timestamp": "2024-01-15T10:00:03Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Getting Started with Semantic Kernel' LIMIT 1),
    'user', 'Can you show me how to create a custom skill?', 12, 'gpt-4', '{"timestamp": "2024-01-15T10:01:00Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Getting Started with Semantic Kernel' LIMIT 1),
    'assistant', 'Here''s a simple custom skill example:\n\n```csharp\npublic class MathSkill\n{\n    [SKFunction, Description("Add two numbers")]\n    public string Add(int a, int b)\n    {\n        return (a + b).ToString();\n    }\n    \n    [SKFunction, Description("Calculate factorial")]\n    public async Task<string> Factorial(int n)\n    {\n        long result = 1;\n        for (int i = 2; i <= n; i++)\n            result *= i;\n        return result.ToString();\n    }\n}\n\n// Register the skill\nkernel.ImportSkill(new MathSkill(), "Math");\n```',
    195, 'gpt-4', '{"timestamp": "2024-01-15T10:01:05Z"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Insert messages for Alice's second conversation
INSERT INTO messages (conversation_id, role, content, tokens_used, model, metadata)
VALUES
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Code Review: Authentication Service' LIMIT 1),
    'user', 'Please review this authentication service code for security issues.', 15, 'gpt-4', '{"timestamp": "2024-01-16T14:30:00Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Code Review: Authentication Service' LIMIT 1),
    'assistant', 'I''ll review the authentication service. Key areas to check:\n\n**Security Concerns:**\n1. Password hashing algorithm (use bcrypt/Argon2)\n2. SQL injection prevention (use parameterized queries)\n3. Session token generation (cryptographically secure random)\n4. Rate limiting to prevent brute force\n5. Secure session storage\n\nPlease share the code and I''ll provide specific feedback.',
    125, 'gpt-4', '{"timestamp": "2024-01-16T14:30:04Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Code Review: Authentication Service' LIMIT 1),
    'user', 'Here are my main concerns: 1) Are we properly salting passwords? 2) Is the session timeout appropriate?', 22, 'gpt-4', '{"timestamp": "2024-01-16T14:32:00Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Code Review: Authentication Service' LIMIT 1),
    'assistant', '**Password Salting:**\n✓ bcrypt automatically handles salting - each hash includes a unique salt\n✓ Cost factor of 12 is good for 2024 standards\n\n**Session Timeout:**\nYour current 24-hour timeout is reasonable for most applications. Consider:\n- Reduce to 8 hours for sensitive applications\n- Implement "remember me" with refresh tokens\n- Add sliding expiration (extend on activity)\n- Force re-auth for critical operations\n\n**Recommendation:** Implement refresh tokens with 7-day expiry and 1-hour access tokens.',
    180, 'gpt-4', '{"timestamp": "2024-01-16T14:32:06Z"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Insert messages for Alice's third conversation
INSERT INTO messages (conversation_id, role, content, tokens_used, model, metadata)
VALUES
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Data Analysis: Sales Trends' LIMIT 1),
    'user', 'Analyze our Q4 sales data and identify trends.', 12, 'gpt-4', '{"timestamp": "2024-01-17T09:00:00Z"}'::jsonb),
  ((SELECT id FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = 'alice' LIMIT 1) AND title = 'Data Analysis: Sales Trends' LIMIT 1),
    'assistant', 'I''ll help analyze your Q4 sales data. To provide insights, I need:\n\n1. Sales data format (CSV, database query, Excel?)\n2. Key metrics to analyze:\n   - Revenue by product/category\n   - Geographic distribution\n   - Customer segments\n   - Time-based trends (daily/weekly/monthly)\n3. Comparison period (Q3? Previous year Q4?)\n4. Specific questions or concerns\n\nPlease share the data or connect to your data source.',
    145, 'gpt-4', '{"timestamp": "2024-01-17T09:00:04Z"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Create sample conversations for Bob
INSERT INTO conversations (id, user_id, title, context, metadata)
SELECT uuid_generate_v4(), (SELECT id FROM users WHERE username = 'bob' LIMIT 1),
       title, context::jsonb, metadata::jsonb
FROM (VALUES
  ('Debugging Performance Issue', '{"max_tokens": 2000, "temperature": 0.2, "model": "gpt-4"}', '{"tags": ["debugging", "performance"], "priority": "high"}'),
  ('Database Schema Design', '{"max_tokens": 3000, "temperature": 0.4, "model": "gpt-4"}', '{"tags": ["database", "architecture"], "language": "en"}')
) AS t(title, context, metadata)
ON CONFLICT (user_id, title) DO NOTHING;

-- Create an archived conversation
INSERT INTO conversations (id, user_id, title, is_archived, context)
SELECT uuid_generate_v4(), (SELECT id FROM users WHERE username = 'alice' LIMIT 1), 'Old Project Discussion', TRUE, '{"max_tokens": 1500, "temperature": 0.7}'::jsonb
ON CONFLICT (user_id, title) DO NOTHING;
