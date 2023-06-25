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
from backend.db_utils import DB_Connector


class Weather_API():
    def __init__(self, user_id:int):
        self.user_id = user_id
        db = DB_Connector()
        self.customer = db.read_to_df(f"SELECT * from app.customers where id={user_id} LIMIT 1;")
        self.lat = self.customer.loc[1, "latitude"]
        self.lon = self.customer.loc[1, "longitude"]
        self.api = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,relativehumidity_2m,surface_pressure,windspeed_10m,windspeed_80m,windspeed_120m,windspeed_180m,winddirection_10m,winddirection_80m,winddirection_120m,winddirection_180m,direct_normal_irradiance,direct_normal_irradiance_instant&forecast_days=3&timezone=auto"

    def get(self) -> pd.DataFrame:
        result = requests.get(self.api).text
        df = pd.DataFrame(json.loads(result).get("hourly"))
        timestamp = datetime.now()
        df["api_called_at"] = timestamp
        df["time"] = pd.to_datetime(df["time"])

        # Only take forecasts that are in the future
        df = df.loc[df["time"] > datetime.now()]
        # Now we drop rows that contain missing data. We already did that
        df = df.dropna(axis=1)
        path = os.path.join(".", "weather_forecasts", str(self.user_id), datetime.now().strftime("%Y-%m-%d %H:%m:%S") +".csv")
        df["customer_id"] = self.user_id
        df.to_csv(path, index=None)
        db = DB_Connector()
        db.write_df(df, "app.forecasts")
        return df

class PV_API():
    def __init__(self, user_id:int):
        self.user_id = user_id

    def get(self) -> pd.DataFrame:
        if self.user_id == 1:
            return self._get_user1()
        else:
            raise ValueError("User is not registered yet")

    def _get_user1(self) -> pd.DataFrame:
        '''
            Queries for the last 365 days
        '''
        starttime = datetime.now() - timedelta(days=365)
        endtime = datetime.now()
        api = f"https://api.solar.sheffield.ac.uk/pvlive/api/v4/pes/12?start={starttime}&end={endtime}&data_format=csv"
        result = requests.get(api).content

        df = pd.read_csv(io.StringIO(result.decode('utf-8')))
        # London is always customer 1
        df["customer_id"] = "1"

        return df

