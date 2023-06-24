CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.customers
(
    id               BIGSERIAL PRIMARY KEY,
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


CREATE TABLE IF NOT EXISTS app.pvlog
(
    id                    BIGSERIAL PRIMARY KEY,
    pes_id SMALLINT,
    datetime_gmt TIMESTAMP,
    generation_mw FLOAT,
    customer_id BIGSERIAL REFERENCES app.customers(id)
);


CREATE TABLE IF NOT EXISTS app.forecasts
(
    id BIGSERIAL PRIMARY KEY,
    time TIMESTAMP,
    api_called_at VARCHAR,
    hour INT,
    temperature_2m FLOAT,
    relativehumidity_2m FLOAT,
    surface_pressure FLOAT,
    windspeed_10m FLOAT,
    windspeed_80m FLOAT,
    windspeed_120m FLOAT,
    windspeed_180m FLOAT,
    winddirection_10m FLOAT,
    winddirection_80m FLOAT,
    winddirection_120m FLOAT,
    winddirection_180m FLOAT,
    direct_normal_irradiance FLOAT,
    is_day DOUBLE PRECISION,
    direct_normal_irradiance_instant FLOAT,
    terrestrial_radiation FLOAT,
    customer_id BIGSERIAL REFERENCES app.customers(id)
);

COMMENT ON COLUMN app.forecasts.api_called_at IS 'The time we called the Weather API to get the weather forecast';
COMMENT ON COLUMN app.forecasts.hour IS 'The hour of the day, the forecast is for';
COMMENT ON COLUMN app.forecasts.time IS 'The time the forecast wants to predict';