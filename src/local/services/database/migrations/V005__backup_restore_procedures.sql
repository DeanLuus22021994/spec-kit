-- Migration: V005 - Backup and Restore Procedures
-- Description: Add database backup metadata tracking and restore points
-- Author: System
-- Date: 2024

-- Backup metadata table
CREATE TABLE IF NOT EXISTS backup_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backup_name VARCHAR(255) NOT NULL UNIQUE,
    backup_type VARCHAR(50) CHECK (backup_type IN ('full', 'incremental', 'differential')),
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    compression VARCHAR(20),
    database_version VARCHAR(20),
    schema_version VARCHAR(50),
    table_count INTEGER,
    row_count BIGINT,
    backup_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    backup_completed_at TIMESTAMP WITH TIME ZONE,
    backup_duration_ms INTEGER,
    created_by VARCHAR(100) DEFAULT CURRENT_USER,
    status VARCHAR(20) CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    error_message TEXT,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for backup queries
CREATE INDEX IF NOT EXISTS idx_backup_metadata_created_at
    ON backup_metadata(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_backup_metadata_status
    ON backup_metadata(status, created_at DESC);

-- Restore history table
CREATE TABLE IF NOT EXISTS restore_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backup_id UUID REFERENCES backup_metadata(id) ON DELETE SET NULL,
    restore_point_time TIMESTAMP WITH TIME ZONE,
    restore_type VARCHAR(50) CHECK (restore_type IN ('full', 'partial', 'point_in_time')),
    tables_restored TEXT[],
    rows_restored BIGINT,
    restore_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    restore_completed_at TIMESTAMP WITH TIME ZONE,
    restore_duration_ms INTEGER,
    performed_by VARCHAR(100) DEFAULT CURRENT_USER,
    status VARCHAR(20) CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for restore history queries
CREATE INDEX IF NOT EXISTS idx_restore_history_created_at
    ON restore_history(created_at DESC);

-- Function to get database statistics for backup
CREATE OR REPLACE FUNCTION get_database_statistics()
RETURNS TABLE (
    total_tables BIGINT,
    total_rows BIGINT,
    total_size_bytes BIGINT,
    table_details JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_tables,
        SUM(n_live_tup)::BIGINT as total_rows,
        SUM(pg_total_relation_size(schemaname||'.'||tablename))::BIGINT as total_size_bytes,
        jsonb_agg(
            jsonb_build_object(
                'table', tablename,
                'rows', n_live_tup,
                'size_bytes', pg_total_relation_size(schemaname||'.'||tablename),
                'size_human', pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
            ) ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        ) as table_details
    FROM pg_stat_user_tables;
END;
$$ LANGUAGE plpgsql;

-- Function to record backup start
CREATE OR REPLACE FUNCTION start_backup(
    p_backup_name VARCHAR(255),
    p_backup_type VARCHAR(50),
    p_file_path TEXT
)
RETURNS UUID AS $$
DECLARE
    v_backup_id UUID;
    v_stats RECORD;
BEGIN
    -- Get current database statistics
    SELECT * INTO v_stats FROM get_database_statistics();

    -- Insert backup record
    INSERT INTO backup_metadata (
        backup_name,
        backup_type,
        file_path,
        table_count,
        row_count,
        backup_started_at,
        status,
        schema_version
    )
    VALUES (
        p_backup_name,
        p_backup_type,
        p_file_path,
        v_stats.total_tables,
        v_stats.total_rows,
        CURRENT_TIMESTAMP,
        'in_progress',
        (SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1)
    )
    RETURNING id INTO v_backup_id;

    RETURN v_backup_id;
END;
$$ LANGUAGE plpgsql;

-- Function to complete backup
CREATE OR REPLACE FUNCTION complete_backup(
    p_backup_id UUID,
    p_file_size_bytes BIGINT,
    p_checksum VARCHAR(64),
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_start_time TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT backup_started_at INTO v_start_time
    FROM backup_metadata
    WHERE id = p_backup_id;

    UPDATE backup_metadata
    SET
        backup_completed_at = CURRENT_TIMESTAMP,
        backup_duration_ms = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v_start_time)) * 1000,
        file_size_bytes = p_file_size_bytes,
        checksum = p_checksum,
        status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
        error_message = p_error_message
    WHERE id = p_backup_id;
END;
$$ LANGUAGE plpgsql;

-- Function to start restore
CREATE OR REPLACE FUNCTION start_restore(
    p_backup_id UUID,
    p_restore_type VARCHAR(50),
    p_tables TEXT[] DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_restore_id UUID;
BEGIN
    INSERT INTO restore_history (
        backup_id,
        restore_type,
        tables_restored,
        restore_started_at,
        status
    )
    VALUES (
        p_backup_id,
        p_restore_type,
        p_tables,
        CURRENT_TIMESTAMP,
        'in_progress'
    )
    RETURNING id INTO v_restore_id;

    RETURN v_restore_id;
END;
$$ LANGUAGE plpgsql;

-- Function to complete restore
CREATE OR REPLACE FUNCTION complete_restore(
    p_restore_id UUID,
    p_rows_restored BIGINT,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_start_time TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT restore_started_at INTO v_start_time
    FROM restore_history
    WHERE id = p_restore_id;

    UPDATE restore_history
    SET
        restore_completed_at = CURRENT_TIMESTAMP,
        restore_duration_ms = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v_start_time)) * 1000,
        rows_restored = p_rows_restored,
        status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
        error_message = p_error_message
    WHERE id = p_restore_id;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old backups
CREATE OR REPLACE FUNCTION cleanup_old_backups(
    p_keep_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    deleted_count INTEGER,
    freed_bytes BIGINT
) AS $$
DECLARE
    v_deleted INTEGER;
    v_freed BIGINT;
BEGIN
    SELECT COUNT(*), COALESCE(SUM(file_size_bytes), 0)
    INTO v_deleted, v_freed
    FROM backup_metadata
    WHERE created_at < CURRENT_TIMESTAMP - (p_keep_days || ' days')::INTERVAL
      AND status = 'completed';

    DELETE FROM backup_metadata
    WHERE created_at < CURRENT_TIMESTAMP - (p_keep_days || ' days')::INTERVAL
      AND status = 'completed';

    RETURN QUERY SELECT v_deleted, v_freed;
END;
$$ LANGUAGE plpgsql;

-- View for backup overview
CREATE OR REPLACE VIEW v_backup_overview AS
SELECT
    b.id,
    b.backup_name,
    b.backup_type,
    b.status,
    b.file_size_bytes,
    pg_size_pretty(b.file_size_bytes) as file_size,
    b.backup_started_at,
    b.backup_completed_at,
    b.backup_duration_ms,
    ROUND(b.backup_duration_ms::NUMERIC / 1000, 2) as backup_duration_sec,
    b.table_count,
    b.row_count,
    b.schema_version,
    b.created_at,
    CASE
        WHEN b.status = 'completed' THEN
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - b.backup_completed_at)) / 86400
        ELSE NULL
    END as age_days
FROM backup_metadata b
ORDER BY b.created_at DESC;

-- Record migration
INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
VALUES ('005', 'Add backup and restore procedures', 0, md5('V005__backup_restore_procedures.sql'))
ON CONFLICT (version) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✓ Migration V005 completed: Backup/restore procedures created';
    RAISE NOTICE '✓ Backup metadata tracking enabled';
    RAISE NOTICE '✓ Restore history tracking enabled';
END $$;
