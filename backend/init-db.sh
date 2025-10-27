#!/bin/bash
set -e

# Locate the pg_hba.conf file and append a trust rule for TCP connection
PG_HBA=$(find /etc/postgresql -name pg_hba.conf | head -n 1)

echo "Adding trust rule to file: $PG_HBA"
echo "host all all all trust" >> "$PG_HBA"



