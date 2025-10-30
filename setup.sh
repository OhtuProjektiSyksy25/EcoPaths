#!/bin/bash

set -e

echo "Starting Docker Compose..."
docker compose up -d

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432 -U pathplanner > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL is ready!"

echo "Populating default area: berlin (walking)..."
inv reset-and-populate-area --area=berlin --network-type=walking

echo "Creating test database if it doesn't exist..."
PGPASSWORD=sekret psql -h localhost -U pathplanner -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'ecopaths_test'" | grep -q 1 || \
PGPASSWORD=sekret psql -h localhost -U pathplanner -d postgres -c "CREATE DATABASE ecopaths_test;"
PGPASSWORD=sekret psql -h localhost -U pathplanner -d ecopaths_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"

echo "Creating and populating test database: ecopaths_test (testarea, walking)..."
export ENV=test
inv reset-and-populate-area --area=testarea --network-type=walking

echo "Setup complete! Your development environment is ready."
