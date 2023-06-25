# HOW TO RUN THE DATABASE

## RUN
1. `docker compose up --build pgdb backend`
2. `docker compose build solai`
3. `docker compose run --rm solai 1`

## If you want to check the database tables
1. `docker compose exec postgres bash`
2. `psql --username postgres postgres`
3. `SELECT * FROM app.forecasts;`