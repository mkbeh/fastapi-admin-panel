#!/bin/bash

set -e

# Create second database for auto tests.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE tests;
EOSQL
