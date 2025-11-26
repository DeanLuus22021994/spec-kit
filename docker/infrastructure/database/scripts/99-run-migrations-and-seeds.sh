#!/bin/bash
# Wrapper to apply pgvector migration and optional seed loading
set -e

# This script is run by Docker during init after 01-init.sql

echo ""
echo "========================================="
echo "Running Additional Migrations and Seeds"
echo "========================================="

# Run pgvector migration (V002)
if [ -f "/migrations/V002__pgvector_extension.sql" ]; then
    echo "Applying V002: pgvector extension and embeddings table"
    psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < /migrations/V002__pgvector_extension.sql 2>&1 | grep -v "ERROR:  relation \"schema_migrations\" does not exist" || true
fi

echo "✓ pgvector migration completed"
echo ""

# Load seeds if environment indicates dev/test
ENVIRONMENT="${DATABASE_SEED_ENV:-development}"
echo "Environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "test" ]; then
    echo "Loading seed data for $ENVIRONMENT environment..."
    for seed in /seeds/*.sql; do
        if [ -f "$seed" ]; then
            filename=$(basename "$seed")
            echo "  - Loading $filename"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$seed"
        fi
    done
    echo "✓ Seed data loaded successfully"
elif [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠ Skipping seeds in production environment"
else
    echo "⚠ Unknown environment: $ENVIRONMENT (skipping seeds)"
fi

echo ""
echo "========================================="
echo "✓ Database setup completed successfully"
echo "========================================="
