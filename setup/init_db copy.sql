CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.customers
(
    customer_id               BIGSERIAL PRIMARY KEY,
    customer_name,            VARCHAR          NOT NULL,
    city                      VARCHAR          NOT NULL,
    latitude                  DOUBLE PRECISION NOT NULL,
    longitude                 DOUBLE PRECISION NOT NULL
);

COMMENT ON COLUMN app.customers.customer_name IS 'Full name of the customer';
COMMENT ON COLUMN app.customers.city IS 'Origin city where the customer is located';
COMMENT ON COLUMN app.customers.latitude IS 'Exact GPS Latitude of the customers PV Station';
COMMENT ON COLUMN app.customers.longitude IS 'Exact GPC Longitude of the customers PV Station';

INSERT INTO app.customers (name, city, latitude, longitude)
VALUES ('LondonElectrics', "London", 31.4, 22.3);


'''CREATE TABLE IF NOT EXISTS app.pv_log
(
    log_id                    BIGSERIAL PRIMARY KEY,
    log_time TIMESTAMP,
    output FLOAT,
    CONSTRAINT customer_id
    FOREIGN KEY(customer_id) 
        REFERENCES customers(customer_id)
);'''

