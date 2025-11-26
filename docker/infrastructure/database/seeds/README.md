# Database Seed Data

This directory contains seed data scripts for development, testing, and demo environments.

## Purpose

Seed data provides:

- Development user accounts for testing
- Sample conversations and messages
- Example skills and plugins
- Demo embeddings and semantic memories
- Test data for quality assurance

## Files

- **001_dev_users.sql** - Development user accounts with various roles
- **002_sample_conversations.sql** - Sample conversation history
- **003_demo_skills.sql** - Demo skills and plugins
- **004_test_embeddings.sql** - Sample embedding data
- **005_api_test_data.sql** - API usage tracking test data

## Usage

Seed data is automatically loaded in **development** and **test** environments only.

### Manual Loading

```bash
# Load specific seed file
docker-compose exec database psql -U user -d semantic_kernel -f /seeds/001_dev_users.sql

# Load all seeds in order
for file in /seeds/*.sql; do
    docker-compose exec database psql -U user -d semantic_kernel -f "$file"
done
```

### Environment-Specific Loading

Seeds are controlled by the `DATABASE_SEED_ENV` environment variable:

- `development` - Load all seed data
- `test` - Load test-specific data only
- `production` - **DO NOT** load seed data

## Important Notes

⚠️ **Never load seed data in production environments!**

- Seed data contains default passwords and test credentials
- Data is intended for development/testing only
- Production data should come from migrations or data imports

## Credentials in Seed Data

All seed users have the password: `Dev@12345`

Default accounts:

- `admin` / `Dev@12345` - Administrator
- `developer` / `Dev@12345` - Developer
- `testuser` / `Dev@12345` - Standard user
- `readonly` / `Dev@12345` - Read-only user

**Change all passwords immediately in any shared environment!**
