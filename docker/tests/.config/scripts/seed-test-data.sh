#!/bin/bash
set -e

echo "🌱 Seeding test data..."
echo "====================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
DB_HOST="${DB_HOST:-database}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-user}"
DB_NAME="${DB_NAME:-semantic_kernel_test}"
DB_PASSWORD="${DB_PASSWORD:-test_password}"
MAX_RETRIES=30
RETRY_DELAY=2

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✅${NC} $message"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠️${NC} $message"
    else
        echo -e "${RED}❌${NC} $message"
    fi
}

# Wait for database with timeout and retries
echo ""
echo "1️⃣ Waiting for database to be ready..."
RETRIES=0
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &> /dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        print_status "fail" "Database not ready after ${MAX_RETRIES} attempts"
        exit 1
    fi
    echo "⏳ Attempt $RETRIES/$MAX_RETRIES - Waiting for database..."
    sleep $RETRY_DELAY
done

print_status "pass" "Database is ready (took $RETRIES attempts)"

# Wait for backend service health check
echo ""
echo "2️⃣ Waiting for backend service..."
RETRIES=0
until curl -f http://backend:80/health &> /dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        print_status "warn" "Backend not ready after ${MAX_RETRIES} attempts (proceeding anyway)"
        break
    fi
    echo "⏳ Attempt $RETRIES/$MAX_RETRIES - Waiting for backend..."
    sleep $RETRY_DELAY
done

if [ $RETRIES -lt $MAX_RETRIES ]; then
    print_status "pass" "Backend service is ready"
fi

# Seed test data with error handling
echo ""
echo "3️⃣ Inserting test data..."

export PGPASSWORD="$DB_PASSWORD"

# Seed users
echo "Seeding users..."
if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL 2>/dev/null
    INSERT INTO users (email, name, created_at) VALUES
        ('test@example.com', 'Test User', NOW()),
        ('admin@example.com', 'Admin User', NOW())
    ON CONFLICT (email) DO NOTHING;
EOSQL
then
    print_status "pass" "Users seeded"
else
    print_status "warn" "User seeding failed (table may not exist yet)"
fi

# Seed conversations
echo "Seeding conversations..."
if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL 2>/dev/null
    INSERT INTO conversations (user_id, title, created_at) VALUES
        (1, 'Test Conversation 1', NOW()),
        (1, 'Test Conversation 2', NOW())
    ON CONFLICT DO NOTHING;
EOSQL
then
    print_status "pass" "Conversations seeded"
else
    print_status "warn" "Conversation seeding failed (table may not exist yet)"
fi

# Seed embeddings (if vector extension is enabled)
echo "Seeding embeddings..."
if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL 2>/dev/null
    INSERT INTO embeddings (conversation_id, content, vector) VALUES
        (1, 'Sample test content', '[0.1, 0.2, 0.3]'::vector)
    ON CONFLICT DO NOTHING;
EOSQL
then
    print_status "pass" "Embeddings seeded"
else
    print_status "warn" "Embedding seeding failed (pgvector may not be enabled)"
fi

# Validate seeded data
echo ""
echo "4️⃣ Validating seeded data..."

# Count users
USER_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users WHERE email IN ('test@example.com', 'admin@example.com');" 2>/dev/null | xargs || echo "0")
if [ "$USER_COUNT" -ge 2 ]; then
    print_status "pass" "Found $USER_COUNT test users"
else
    print_status "warn" "Expected 2 users, found $USER_COUNT"
fi

# Count conversations
CONV_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM conversations WHERE user_id = 1;" 2>/dev/null | xargs || echo "0")
if [ "$CONV_COUNT" -ge 2 ]; then
    print_status "pass" "Found $CONV_COUNT test conversations"
else
    print_status "warn" "Expected 2 conversations, found $CONV_COUNT"
fi

# Count embeddings
EMB_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM embeddings WHERE conversation_id = 1;" 2>/dev/null | xargs || echo "0")
if [ "$EMB_COUNT" -ge 1 ]; then
    print_status "pass" "Found $EMB_COUNT test embeddings"
else
    print_status "warn" "Expected 1+ embeddings, found $EMB_COUNT"
fi

# Summary
echo ""
echo "====================="
echo "Seeding Summary"
echo "====================="
echo "Users: $USER_COUNT"
echo "Conversations: $CONV_COUNT"
echo "Embeddings: $EMB_COUNT"
echo ""

if [ "$USER_COUNT" -ge 2 ] && [ "$CONV_COUNT" -ge 2 ]; then
    print_status "pass" "Test data seeding completed successfully"
    exit 0
else
    print_status "warn" "Test data seeding completed with warnings"
    echo ""
    echo "Some tables may not exist yet. This is normal for fresh databases."
    echo "Run database migrations first: make db-migrate"
    exit 0  # Don't fail, just warn
fi
