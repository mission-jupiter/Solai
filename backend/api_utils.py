import requests
from datetime import datetime, timedelta
import pandas as pd
import io
import os
import json
from backend.db_utils import DB_Connector


class Weather_API:
    """Weather_API manages the access to the open-meteo API"""

    def __init__(self, user_id: int):
        """
        Args:
            user_id (int): Unique user_id to identify the PV location
        """
        self.user_id = user_id
        db = DB_Connector()
        self.customer = db.read_to_df(
            f"SELECT * from app.customers where id={user_id} LIMIT 1;"
        )
        self.lat = self.customer.loc[1, "latitude"]
        self.lon = self.customer.loc[1, "longitude"]
        self.api = (
            f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&"
            f"longitude={self.lon}&hourly=temperature_2m,relativehumidity_2m,"
            "surface_pressure,windspeed_10m,windspeed_80m,windspeed_120m,"
            "windspeed_180m,winddirection_10m,winddirection_80m,"
            "winddirection_120m,winddirection_180m,direct_normal_irradiance,"
            "direct_normal_irradiance_instant&forecast_days=3&timezone=auto"
        )

    def get(self) -> pd.DataFrame:
        """get Performs the API call and returns the result in a pd.DataFrame

        Returns:
            pd.DataFrame: API result + preprocessing steps
        """
        result = requests.get(self.api).text
        df = pd.DataFrame(json.loads(result).get("hourly"))

        # We add specific timestamp columns
        timestamp = datetime.now()
        df["api_called_at"] = timestamp
        df["time"] = pd.to_datetime(df["time"])

        # Only take forecasts that are in the future
        df = df.loc[df["time"] > datetime.now()]
        # Now we drop rows that contain missing data. We already did that
        df = df.dropna(axis=1)
        path = os.path.join(
            ".",
            "weather_forecasts",
            str(self.user_id),
            datetime.now().strftime("%Y-%m-%d %H:%m:%S") + ".csv",
        )
        # Adding the customer_id
        df["customer_id"] = self.user_id
        df.to_csv(path, index=None)

        # Storing the df into the database
        db = DB_Connector()
        db.write_df(df, "app.forecasts")
        return df


class PV_API:
    """PV_API receives the last 365 days for the requested users pv station"""

    def __init__(self, user_id: int):
        """
        Args:
            user_id (int): Unique user id
        """
        self.user_id = user_id

    def get(self) -> pd.DataFrame:
        """get Manually defined method to map user_id to a specific API

        Raises:
            ValueError: Notifies us if the requested user is not mapped to a
            API

        Returns:
            pd.DataFrame: returns the resulting DataFrame
        """
        if self.user_id == 1:
            df = self._get_user1()
            return df
        else:
            raise ValueError("User is not registered yet")

    def _get_user1(self) -> pd.DataFrame:
        """
        Queries for the last 365 days for user 1
        """
        starttime = datetime.now() - timedelta(days=365)
        endtime = datetime.now()
        api = (
            "https://api.solar.sheffield.ac.uk/pvlive/api/v4/pes/12?"
            f"start={starttime}&end={endtime}&data_format=csv"
        )
        result = requests.get(api).content

        df = pd.read_csv(io.StringIO(result.decode("utf-8")))
        # London is always customer 1
        df["customer_id"] = "1"
        return df
