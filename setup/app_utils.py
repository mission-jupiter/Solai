import requests
import pydantic
from datetime import datetime, timedelta
from typing import Literal,List,Union
import pandas as pd
import io
import psycopg2
import psycopg2.extras as extras
from io import StringIO
import os
from glob import glob
from pathlib import Path
import json
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn import preprocessing
import pickle
from sklearn.feature_selection import chi2
import numpy as np
from typing import Tuple

# PV APIs
def london_energy_api(hours:int = 48) -> pd.DataFrame():
    '''
    Loads the last 48 hours of PV Output Data from the "London Energy" customers API
    '''
    starttime = datetime.now() - timedelta(hours=hours)
    endtime = datetime.now()
    api = f"https://api.solar.sheffield.ac.uk/pvlive/api/v4/pes/12?start={starttime}&end={endtime}&data_format=csv"
    result = requests.get(api).content
    df = pd.read_csv(io.StringIO(result.decode('utf-8')))
    df["customer_id"] = "1"
    return df

# Weather Forecast APIs
def get_forecast(user_id:int, write_to_db:bool=True, write_to_json:bool=True) -> pd.DataFrame:
    '''
        Takes the user_id, gets the location from the database and calls the Forecast API
    '''
    d = DB_Connector()
    df = d.read_to_df(f"SELECT * from app.customers where id={user_id} LIMIT 1;")
    lat = df.loc[1, "latitude"]
    lon = df.loc[1, "longitude"]
    api = api = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relativehumidity_2m,surface_pressure,windspeed_10m,windspeed_80m,windspeed_120m,windspeed_180m,winddirection_10m,winddirection_80m,winddirection_120m,winddirection_180m,direct_normal_irradiance,direct_normal_irradiance_instant&forecast_days=3&timezone=auto"
    
    result = requests.get(api).text
    forecast = pd.DataFrame(json.loads(result).get("hourly"))
    forecast["time"] = pd.to_datetime(forecast["time"])
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M")
    #breakpoint()
    # Only take forecasts that are in the future
    forecast = forecast.loc[forecast["time"] > datetime.now()]

    if write_to_json:
        forecast.to_json(f"weather_forecasts/{user_id}/{timestamp}.json")

    if write_to_db:
        db = DB_Connector()
        df["api_called_at"] = timestamp
        db.write_df(_forecast_preprocessing(forecast), "app.forecasts")

    return forecast

# Database Connectors
class DB_Connector():
    def __init__(self):
        # Connection has to be closes manually at the end connection.close()
        self.connection = psycopg2.connect(
                host="localhost",
                port="5432",
                database="postgres",
                user="postgres",
                password="postgres"
            )
    
    def write_df(self, df:pd.DataFrame, table:str) -> None:
        """
        Using psycopg2.extras.execute_values() to insert the dataframe
        It's important that the columsn in the given pandas DataFrame have the
        same names like the database table
        Reference: https://naysan.ca/2020/05/09/pandas-to-postgresql-using-psycopg2-bulk-insert-performance-benchmark/
        """
        # Create a list of tupples from the dataframe values
        tuples = [tuple(x) for x in df.to_numpy()]
        # Comma-separated dataframe columns
        cols = ','.join(list(df.columns))
        # SQL quert to execute
        query  = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
        cursor = self.connection.cursor()
        try:
            extras.execute_values(cursor, query, tuples)
            self.connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            self.connection.rollback()
            cursor.close()
            return 1
        print("execute_values() done")
        cursor.close()

    def query(self, query:str) -> str:
        '''
        let's us use all DB queries and returns them as a string
        '''
        with self.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def read_to_df(self, query:str) -> pd.DataFrame:
        '''
        Always take the whole dataframe or at least the Primary key with it,
        because the first column will be taken as index of the DataFrame
        '''
        # closes the cursor after usage
        print("Execute Read")
        with self.connection.cursor() as cur:
            cur.execute(query)
            #columns = [d[0] for d in cur.description]
            df = pd.DataFrame(cur.fetchall())
            cols = [c[0] for c in cur.description]
            df.columns = cols
            df = df.set_index(df.columns[0])
            return df

def _forecast_preprocessing(df:pd.DataFrame) -> pd.DataFrame:
    df["time"] = pd.to_datetime(df["time"])
    df["hour"] = df["time"].dt.hour
    # Now remove all not forecasting timestamps that are smaller than the query time.
    df = df.loc[df["time"] >= df["api_called_at"]]
    return df

def write_forecasts_to_db(user:int):

    path = f"./weather_forecasts/{user}/"
    files = glob(os.path.join(path, "*.json"))
    def df_generator():
        for f in files:
            df = pd.read_json(f)
            df["api_called_at"] = datetime.strptime(Path(f).stem, "%Y-%m-%d_%H:%M")
            yield _forecast_preprocessing(df)

    df = pd.concat(df_generator(), ignore_index=True)
    df["customer_id"] = user

    # Now we filter out duplicates of the time column
    df = df.drop_duplicates(subset="time")
    # Now we drop rows that contain missing data
    df.dropna(axis=1, inplace=True)

    # Now we can load the data into the database
    d = DB_Connector()
    d.write_df(df, "app.forecasts")

def write_pvdata_to_db(user:int):
    df = london_energy_api(8760)
    filepath = f"./pv_data/{user}/historical_pv_data.json"
    # Now we can load the data into the database
    d = DB_Connector()
    df.to_json(filepath)
    d.write_df(df, "app.pvlog")


def get_model() -> None:
    db = DB_Connector()
    forecasts_data = db.read_to_df("SELECT * from app.forecasts;")
    forecasts_data = forecasts_data.rename(columns={'api_called_at': 'merge_time'})
    pv_data = db.read_to_df("SELECT * from app.pvlog;")
    pv_data = pv_data.rename(columns={'datetime_gmt': 'merge_time'})
    pv_data['merge_time'] = pv_data['merge_time'].astype(str)

    merged_data = pd.merge(forecasts_data, pv_data, on='merge_time')

    x = merged_data[['temperature_2m',
                     'relativehumidity_2m',
                     'surface_pressure',
                     'windspeed_10m',
                     'windspeed_80m',
                     'windspeed_120m',
                     'windspeed_180m',
                     'winddirection_10m',
                     'winddirection_80m',
                     'winddirection_120m',
                     'winddirection_180m',
                     'direct_normal_irradiance',
                     'direct_normal_irradiance_instant']]

    y = merged_data['generation_mw']
    breakpoint()
    model = LinearRegression()
    pred_model = model.fit(x, y)
    return pred_model

def _create_training_data() -> pd.DataFrame:
    '''
    This function is used to create the training and testings data for the
    ML model
    '''
    db = DB_Connector()
    forecasts_data = db.read_to_df("SELECT * from app.forecasts;")
    forecasts_data = forecasts_data.drop(columns=["customer_id","hour"])
    pv_data = db.read_to_df("SELECT * from app.pvlog;")
    pv_data = pv_data.drop(columns=["customer_id", "pes_id"])

    merged_data = pd.merge(forecasts_data, pv_data, left_on="time", right_on="datetime_gmt", how="inner")
    merged_data = merged_data.drop(columns=["datetime_gmt"])
    merged_data = merged_data[["direct_normal_irradiance_instant", "generation_mw"]]

    return merged_data


def train_model():

    df =  _create_training_data()
    x = df["direct_normal_irradiance_instant"].to_numpy().reshape(-1,1)
    y = df["generation_mw"].to_numpy().reshape(-1,1)
    # creating train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=21)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    # Evaluate the model
    # model evaluation
    print("Mean Squared Error", mean_squared_error(y_test, predictions))
    #print("Mean Absolute Error", mean_absolute_error(y_test, predictions))
    print("Model Coefs", model.coef_)
    # saving the model to disk
    pickle.dump(model, open("trained_model.pickle", "wb"))
    #scores, pvalues = chi2(X_train, y_train) 
    #print("Pvalues:", pvalues)


def predict(user_id:int) -> pd.DataFrame:
    data_x = get_forecast(user_id=user_id,  write_to_db=False, write_to_json=False)
    time = data_x["time"]

    x = data_x["direct_normal_irradiance_instant"].to_numpy().reshape(-1,1)
    
    model = pickle.load(open("trained_model.pickle", "rb"))
    pred = model.predict(x)
    df = pd.DataFrame(time, columns=["time"]).set_index("time")
    df["forecast"] = x
    df["pred"] = pred
    return df

def filter_forecast(df) -> pd.DataFrame:
    df = df[['temperature_2m',
            'relativehumidity_2m',
             'surface_pressure',
             'windspeed_10m',
             'windspeed_80m',
             'windspeed_120m',
             'windspeed_180m',
             'winddirection_10m',
             'winddirection_80m',
             'winddirection_120m',
             'winddirection_180m',
             'direct_normal_irradiance',
             'direct_normal_irradiance_instant']]

    return df
