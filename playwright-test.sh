#!/bin/bash
set -e

echo "Starting playwright end-to-end tests..."

# Go to e2e directory
cd "$(dirname "$0")/e2e"

# Ensure dependencies are installed
if [ ! -d "node_modules" ]; then
  echo "Installing E2E test dependencies..."
  npm ci
fi

# Run Playwright tests
npx playwright test

# Capture exit code
exit_code=$?

# Return to root
cd ..

if [ $exit_code -eq 0 ]; then
  echo "E2E tests passed!"
else
  echo "E2E tests failed!"
fi

exit $exit_code
