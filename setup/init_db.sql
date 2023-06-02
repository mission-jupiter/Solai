CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.customers
(
    customer_id               BIGSERIAL PRIMARY KEY,
    customer_name            VARCHAR          NOT NULL,
    city                      VARCHAR          NOT NULL,
    latitude                  DOUBLE PRECISION NOT NULL,
    longitude                 DOUBLE PRECISION NOT NULL
);

COMMENT ON COLUMN app.customers.customer_name IS 'Full name of the customer';
COMMENT ON COLUMN app.customers.city IS 'Origin city where the customer is located';
COMMENT ON COLUMN app.customers.latitude IS 'Exact GPS Latitude of the customers PV Station';
COMMENT ON COLUMN app.customers.longitude IS 'Exact GPC Longitude of the customers PV Station';

INSERT INTO app.customers (customer_name, city, latitude, longitude)
VALUES ('LondonElectrics', 'London', 31.4, 22.3),
        ('SydneySolar', 'Sydney', 11.4, 55.3);


CREATE TABLE IF NOT EXISTS app.pv_log
(
    log_id                    BIGSERIAL PRIMARY KEY,
    log_time TIMESTAMP,
    output FLOAT,
    customer_id BIGSERIAL REFERENCES app.customers(customer_id)
);

INSERT INTO app.pv_log ( log_time, output, customer_id)
VALUES ('2023-04-30 10:00:00', 30, 2),
 ('2023-04-30 11:00:00', 30, 2),
 ('2023-04-30 10:00:00', 50, 1);


 CREATE TABLE IF NOT EXISTS app.forecasts
(
    id                    BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    temp FLOAT,
    customer_id BIGSERIAL REFERENCES app.customers(customer_id)
);

INSERT INTO app.forecasts ( timestamp, temp, customer_id)
VALUES ('2023-04-30 10:00:00', 22.2, 2),
 ('2023-04-30 11:00:00', 23.2, 2),
 ('2023-04-30 10:00:00', 18.0, 1);