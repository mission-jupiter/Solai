# HOW TO RUN THE DATABASE

## RUN
1. `docker compose up --build`


## Here you should see some outputs now
For further looks into the database use:
1. `docker compose exec postgres bash`
2. `psql --username postgres postgres`
3. `SELECT * FROM app.customers;`