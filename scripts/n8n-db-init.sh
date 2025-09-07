#!/usr/bin/env bash
set -Eeuo pipefail

until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER"; do sleep 1; done

# Escape single quotes for SQL literal
esc_pass=${N8N_PASS//\'/\'\'}

# Role
if ! psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${N8N_USER}'" postgres | grep -q 1; then
  psql -v ON_ERROR_STOP=1 -d postgres -c "CREATE ROLE \"${N8N_USER}\" LOGIN PASSWORD '${esc_pass}';"
fi

# DB (owned by role)
if ! psql -tAc "SELECT 1 FROM pg_database WHERE datname='${N8N_DB}'" postgres | grep -q 1; then
  psql -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE \"${N8N_DB}\" OWNER \"${N8N_USER}\" ENCODING 'UTF8';"
fi

# Schema + defaults
psql -v ON_ERROR_STOP=1 -d "$N8N_DB" -c "CREATE SCHEMA IF NOT EXISTS n8n AUTHORIZATION \"${N8N_USER}\";"
psql -v ON_ERROR_STOP=1 -d "$N8N_DB" -c "GRANT ALL PRIVILEGES ON SCHEMA n8n TO \"${N8N_USER}\";"
psql -v ON_ERROR_STOP=1 -d "$N8N_DB" -c "ALTER ROLE \"${N8N_USER}\" IN DATABASE \"${N8N_DB}\" SET search_path TO n8n, public;"
