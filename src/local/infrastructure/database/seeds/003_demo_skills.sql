-- Seed Data: Demo Skills and Plugins
-- Purpose: Create sample skills for testing semantic kernel functionality
-- Environment: Development/Test only

-- Additional demo skills (init.sql already has 4 skills)
INSERT INTO skills (name, description, category, version, is_enabled, configuration) VALUES
    ('EmailGenerator', 'Generate professional email templates', 'Communication', '1.0.0', TRUE,
     '{"tone_options": ["formal", "casual", "friendly"], "max_length": 1000}'::jsonb),
    ('CodeExplainer', 'Explain code in natural language', 'Development', '1.0.0', TRUE,
     '{"supported_languages": ["python", "javascript", "csharp", "java", "go"], "detail_level": "intermediate"}'::jsonb),
    ('MeetingSummarizer', 'Summarize meeting notes and action items', 'Productivity', '1.0.0', TRUE,
     '{"extract_action_items": true, "identify_attendees": true}'::jsonb),
    ('SQLQueryGenerator', 'Generate SQL queries from natural language', 'Database', '1.0.0', TRUE,
     '{"dialects": ["postgresql", "mysql", "sqlserver"], "include_explain": true}'::jsonb),
    ('DocumentQA', 'Answer questions about uploaded documents', 'NLP', '1.0.0', TRUE,
     '{"supported_formats": ["pdf", "docx", "txt"], "context_window": 4000}'::jsonb),
    ('TranslationService', 'Translate text between languages', 'NLP', '1.0.0', TRUE,
     '{"languages": ["en", "es", "fr", "de", "ja", "zh"], "preserve_formatting": true}'::jsonb),
    ('SentimentAnalysis', 'Analyze sentiment of text', 'Analytics', '1.0.0', TRUE,
     '{"granularity": "sentence", "emotions": ["positive", "negative", "neutral", "mixed"]}'::jsonb),
    ('ImageDescriber', 'Generate descriptions of images', 'Vision', '1.0.0', FALSE,
     '{"detail_level": "high", "include_ocr": true, "max_description_length": 500}'::jsonb),
    ('CodeRefactor', 'Suggest code refactoring improvements', 'Development', '1.1.0', TRUE,
     '{"focus_areas": ["performance", "readability", "maintainability"], "apply_solid_principles": true}'::jsonb),
    ('TestGenerator', 'Generate unit tests from code', 'Development', '1.0.0', TRUE,
     '{"frameworks": ["xunit", "nunit", "jest", "pytest"], "coverage_target": 80}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Create sample planner executions
DO $$
DECLARE
    v_alice_id UUID;
    v_bob_id UUID;
    v_skill_summarize UUID;
    v_skill_codegen UUID;
BEGIN
    SELECT id INTO v_alice_id FROM users WHERE username = 'alice' LIMIT 1;
    SELECT id INTO v_bob_id FROM users WHERE username = 'bob' LIMIT 1;
    SELECT id INTO v_skill_summarize FROM skills WHERE name = 'TextSummarization' LIMIT 1;
    SELECT id INTO v_skill_codegen FROM skills WHERE name = 'CodeGeneration' LIMIT 1;

    -- Sample planner execution (completed)
    INSERT INTO planner_executions (user_id, goal, plan, status, steps_completed, total_steps, result, completed_at)
    VALUES
        (v_alice_id, 'Summarize this article and create a tweet about it',
         '[
            {"step": 1, "skill": "TextSummarization", "description": "Summarize the article"},
            {"step": 2, "skill": "ContentGeneration", "description": "Create a tweet from summary"}
         ]'::jsonb,
         'completed', 2, 2,
         '{"summary": "AI advances in 2024", "tweet": "Exciting AI breakthroughs this year! 🚀 #AI #TechNews"}'::jsonb,
         CURRENT_TIMESTAMP - INTERVAL '2 hours');

    -- Sample planner execution (in progress)
    INSERT INTO planner_executions (user_id, goal, plan, status, steps_completed, total_steps)
    VALUES
        (v_bob_id, 'Analyze code for security issues and generate a report',
         '[
            {"step": 1, "skill": "CodeAnalysis", "description": "Scan code for vulnerabilities"},
            {"step": 2, "skill": "ReportGenerator", "description": "Create security report"}
         ]'::jsonb,
         'in_progress', 1, 2);

    -- Sample function executions
    INSERT INTO function_executions (skill_id, function_name, user_id, input_parameters, output_result, execution_time_ms, status)
    VALUES
        (v_skill_summarize, 'Summarize', v_alice_id,
         '{"text": "Long article content...", "max_length": 200}'::jsonb,
         '{"summary": "Brief summary of the article.", "original_length": 1500, "summary_length": 180}'::jsonb,
         245, 'success'),
        (v_skill_codegen, 'GenerateFunction', v_bob_id,
         '{"description": "Create a function to calculate fibonacci", "language": "python"}'::jsonb,
         '{"code": "def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)"}'::jsonb,
         1820, 'success'),
        (v_skill_summarize, 'Summarize', v_alice_id,
         '{"text": "Another article...", "max_length": 150}'::jsonb,
         NULL,
         0, 'error');

    -- Update error message for failed execution
    UPDATE function_executions
    SET error_message = 'Input text too short for summarization (minimum 100 characters)'
    WHERE status = 'error' AND function_name = 'Summarize';

    RAISE NOTICE '✓ Created % demo skills', (SELECT COUNT(*) FROM skills);
    RAISE NOTICE '✓ Created sample planner executions';
    RAISE NOTICE '✓ Created sample function execution logs';
END $$;
