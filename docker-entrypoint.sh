#!/bin/bash
set -e

sed -i "s|\${REACT_APP_MAPBOX_TOKEN}|${REACT_APP_MAPBOX_TOKEN}|g" /app/backend/build/config.js
sed -i "s|\${REACT_APP_MAPBOX_STYLE}|${REACT_APP_MAPBOX_STYLE}|g" /app/backend/build/config.js
sed -i "s|\${REACT_APP_API_URL}|${REACT_APP_API_URL}|g" /app/backend/build/config.js

exec "$@"