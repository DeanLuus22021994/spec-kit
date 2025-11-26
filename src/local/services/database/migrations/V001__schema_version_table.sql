-- Migration: V001 - Create schema version tracking table
-- Description: Tracks which migrations have been applied to the database
-- Author: System
-- Date: 2024

-- Create schema_migrations table to track applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    checksum VARCHAR(64),
    applied_by VARCHAR(100) DEFAULT CURRENT_USER
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
    ON schema_migrations(applied_at DESC);

-- Insert this migration record
INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
VALUES ('001', 'Create schema version tracking table', 0, md5('V001__schema_version_table.sql'))
ON CONFLICT (version) DO NOTHING;

-- Create function to validate migration order
CREATE OR REPLACE FUNCTION validate_migration_order()
RETURNS TRIGGER AS $$
DECLARE
    last_version VARCHAR(50);
BEGIN
    SELECT version INTO last_version
    FROM schema_migrations
    ORDER BY version DESC
    LIMIT 1;

    IF last_version IS NOT NULL AND NEW.version <= last_version THEN
        RAISE EXCEPTION 'Migration version % must be greater than last applied version %',
            NEW.version, last_version;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce migration order
CREATE TRIGGER trg_validate_migration_order
    BEFORE INSERT ON schema_migrations
    FOR EACH ROW
    EXECUTE FUNCTION validate_migration_order();

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✓ Migration V001 completed: Schema version tracking table created';
END $$;
