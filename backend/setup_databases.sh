#!/bin/bash
# backend/setup_databases.sh
# Create production and test databases using settings from .env and .env.test

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Loading environment variables..."

# Load .env
if [ -f "$SCRIPT_DIR/.env" ]; then
  echo "→ Loaded .env from $SCRIPT_DIR/.env"
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
else
  echo ".env not found at $SCRIPT_DIR/.env"
fi

# Set default values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
# Development (dev) database
DEV_USER="${DB_USER:-postgres}"
DEV_PASSWORD="${DB_PASSWORD:-postgres}"
DEV_DB="${DB_NAME:-ecopaths}"

echo "DEBUG: After .env → DB_USER=$DB_USER"

# Load .env.test
if [ -f "$SCRIPT_DIR/.env.test" ]; then
  echo "→ Loaded .env.test from $SCRIPT_DIR/.env.test"
  set -a
  source "$SCRIPT_DIR/.env.test"
  set +a
else
  echo ".env.test not found at $SCRIPT_DIR/.env.test"
fi

# Test database
TEST_USER="${DB_USER_TEST:-postgres}"
TEST_PASSWORD="${DB_PASSWORD_TEST:-postgres}"
TEST_DB="${DB_NAME_TEST:-ecopaths_test}"

echo "→ Using DEV_DB=$DEV_DB and DEV_USER=$DEV_USER for development"
echo "→ Using TEST_DB=$TEST_DB and TEST_USER=$TEST_USER for testing"

echo "Creating local development database '$DEV_DB'..."
psql -h "$DB_HOST" -U "$DEV_USER" -p "$DB_PORT" -d postgres -c "DROP DATABASE IF EXISTS $DEV_DB;"
psql -h "$DB_HOST" -U "$DEV_USER" -p "$DB_PORT" -d postgres -c "CREATE DATABASE $DEV_DB;"
psql -h "$DB_HOST" -U "$DEV_USER" -p "$DB_PORT" -d "$DEV_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -h "$DB_HOST" -U "$DEV_USER" -p "$DB_PORT" -d "$DEV_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
echo "Local development database ready."

echo "Creating test database '$TEST_DB'..."
psql -h "$DB_HOST" -U "$TEST_USER" -p "$DB_PORT" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"
psql -h "$DB_HOST" -U "$TEST_USER" -p "$DB_PORT" -d postgres -c "CREATE DATABASE $TEST_DB;"
psql -h "$DB_HOST" -U "$TEST_USER" -p "$DB_PORT" -d "$TEST_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -h "$DB_HOST" -U "$TEST_USER" -p "$DB_PORT" -d "$TEST_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
echo "Test database ready."

echo "Creating test tables in '$TEST_DB'..."

poetry run python -c "
import os
os.environ['ENV'] = 'test'
from src.database.db_client import DatabaseClient
db = DatabaseClient()
area = 'testarea'
network_type = 'walking'
db.create_tables_for_area(area, network_type)
"

echo "Test tables created in '$TEST_DB'."
