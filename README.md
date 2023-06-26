# Project Description
The SolAI Service wants to predict the output of specific
PV-Stations for specific customers.
The application offers three services:

### **1. pgdb**: A local postgres Database

The datase consists of three tables:

- The **customers** table stores all information about our customers -> their names, the location of their pv-station and a unique user_id.

- **pvlog** stores the output of all pvstations for the last 365 days. Right now it gets populated via an API Call, for future implementations this would change to an incremental update cycle to reduce the load on the API requests.

- The most important table is **forecasts** which gets populated from .csv files stored in **weather_forecasts**. The folder *weather_forecasts* acts as a local S3 Bucket replacement, where we would store all Forecast API results. Because we know which columns we need, a database is the most suitable option for this project. 

### **2. backend**: An application that sets up the database tables and trains the Machine Learning Model

The backend is run in **app.py**, which does two things:

1. **Initialize the Database**

    This is done by taking the stored .csv files in **weather_forecasts**. For every weather forecast API call, we preprocess the result and store it as a .csv file. Later on we would change that to a S3 Bucket.

    Those stored forecasts are loaded into the **forecasts** table on initialization.

    Afterwards we call the **PV API** that requests the data for the desired PV station for the last 365 days. We store the result in the **pvlog** table.

2. **Train the ML model**

    We use the **pvlog** table and the **forecasts** table to create a training set. For now we just use one independent variable. This can be expanded after a sophisticated statistical analysis.


### **3. SolAI**:

SolAI is just a lightweight container that uses the pretrained model to make a prediction. To function it uses the **Weather API** to get a weather forecast for the location, that is defined for the **user_id**.


# How to run the project
For the project you need to install and run your local docker engine.

## Starting the Database and the backend
1. `docker compose up -d --build pgdb backend`

## Predict the PV Output
Replace 1 with your user_id. Right now there is just user=1 usable
1. `docker compose build solai`
2. `docker compose run --rm solai 1`

## If you want to check the database tables
1. `docker compose exec postgres bash`
2. `psql --username postgres postgres`
3. `SELECT * FROM app.forecasts;`