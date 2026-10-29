# One-command reproduction of Phase 1A. Run from project root.
$ErrorActionPreference = "Stop"

Write-Host "== 1. Staging build ==" -ForegroundColor Cyan
python scripts/01_build_staging.py

Write-Host "`n== 2. Start Postgres ==" -ForegroundColor Cyan
docker compose up -d
Start-Sleep -Seconds 3
$h = docker inspect --format='{{.State.Health.Status}}' retail_pg
while ($h -ne "healthy") {
    Write-Host "   waiting for healthy ($h)..."
    Start-Sleep -Seconds 2
    $h = docker inspect --format='{{.State.Health.Status}}' retail_pg
}

Write-Host "`n== 3. Schema ==" -ForegroundColor Cyan
docker compose exec -T postgres psql -U retail -d retail -v ON_ERROR_STOP=1 -f /sql/01_schema.sql

Write-Host "`n== 4. COPY staging ==" -ForegroundColor Cyan
$tables = @("stg_line_items","stg_event_calendar","stg_store_summary","stg_item_summary")
foreach ($t in $tables) {
    docker compose exec -T postgres psql -U retail -d retail -v ON_ERROR_STOP=1 -c "\copy retail.$t FROM '/data/processed/$t.csv' WITH (FORMAT csv, HEADER true)"
}

Write-Host "`n== 5. Transform to star ==" -ForegroundColor Cyan
docker compose exec -T postgres psql -U retail -d retail -v ON_ERROR_STOP=1 -f /sql/02_transform_to_star.sql

Write-Host "`n== 6. Validation ==" -ForegroundColor Cyan
docker compose exec -T postgres psql -U retail -d retail -v ON_ERROR_STOP=1 -f /sql/03_validation_tests.sql

Write-Host "`n== Phase 1A complete ==" -ForegroundColor Green