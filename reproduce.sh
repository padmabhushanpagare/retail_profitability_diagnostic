#!/bin/bash
set -e
echo "1. Starting Postgres..."
docker compose up -d
sleep 5

echo "2. Building staging data..."
python scripts/01_build_staging.py

echo "3. Creating Schema..."
docker compose exec -T postgres psql -U retail -d retail -f /sql/01_schema.sql

echo "4. Copying Data..."
docker compose exec -T postgres psql -U retail -d retail -c "\copy retail.stg_line_items FROM '/data/processed/stg_line_items.csv' WITH (FORMAT csv, HEADER true)"
docker compose exec -T postgres psql -U retail -d retail -c "\copy retail.stg_event_calendar FROM '/data/processed/stg_event_calendar.csv' WITH (FORMAT csv, HEADER true)"
docker compose exec -T postgres psql -U retail -d retail -c "\copy retail.stg_store_summary FROM '/data/processed/stg_store_summary.csv' WITH (FORMAT csv, HEADER true)"
docker compose exec -T postgres psql -U retail -d retail -c "\copy retail.stg_item_summary FROM '/data/processed/stg_item_summary.csv' WITH (FORMAT csv, HEADER true)"

echo "5. Running Transformation and Validation..."
docker compose exec -T postgres psql -U retail -d retail -f /sql/02_transform_to_star.sql
docker compose exec -T postgres psql -U retail -d retail -f /sql/03_validation_tests.sql

echo "Reproduction Complete. Check output for 'ALL CHECKS PASSED'."