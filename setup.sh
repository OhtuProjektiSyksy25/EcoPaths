#!/bin/bash

set -e

echo "Starting Database via Docker Compose..."
docker compose up -d db

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432 -U pathplanner > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL is ready!"

echo "Populating all areas..."
inv reset-and-populate-area --area=testarea
inv reset-and-populate-area --area=berlin
inv reset-and-populate-area --area=helsinki
inv reset-and-populate-area --area=london
inv reset-and-populate-area --area=la
inv reset-and-populate-area --area=riyadh
inv reset-and-populate-area --area=rome

echo "Creating test database if it doesn't exist..."
PGPASSWORD=sekret psql -h localhost -U pathplanner -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'ecopaths_test'" | grep -q 1 || \
PGPASSWORD=sekret psql -h localhost -U pathplanner -d postgres -c "CREATE DATABASE ecopaths_test;"
PGPASSWORD=sekret psql -h localhost -U pathplanner -d ecopaths_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"

echo "Creating and populating test database: ecopaths_test (testarea, walking)..."
export ENV=test
inv reset-and-populate-area --area=testarea

echo "Setup complete! Your development environment is ready."
