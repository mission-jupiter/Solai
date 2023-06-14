import requests
import pydantic
from datetime import datetime, timedelta
from typing import Literal,List,Union
import pandas as pd
import io
import psycopg2
import psycopg2.extras as extras
from io import StringIO

# PV APIs
def london_energy_api() -> pd.DataFrame():
    '''
    Loads the last 48 hours of PV Output Data from the "London Energy" customers API
    '''
    starttime = datetime.now() - timedelta(hours=48)
    endtime = datetime.now()
    api = f"https://api.solar.sheffield.ac.uk/pvlive/api/v4/pes/12?start={starttime}&end={endtime}&data_format=csv"
    result = requests.get(api).content

    df = pd.read_csv(io.StringIO(result.decode('utf-8')))
    return df

# Weather Forecast APIs
def get_forecast(user_id:int):
    '''
        Takes the user_id, gets the location from the database and calls the Forecast API
    '''
    d = DB_Connector()
    df = d.read(f"SELECT lat, lon from app.users where id={user_id} LIMIT 1;")[0]
    lat = df["lat"]
    lon = df["lon"]
    api = api = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relativehumidity_2m,surface_pressure,windspeed_10m,winddirection_10m,is_day,terrestrial_radiation&current_weather=true&forecast_days=3&timezone=auto"
    result = requests.get(api).content
    df = pd.read_csv(io.StringIO(result.decode('utf-8')))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M")
    df.to_json(f"forecast-data/{timestamp}.json")


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
    
    def write(self, df:pd.DataFrame, table:str) -> None:
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



    def read(self, query:str) -> pd.DataFrame:
        # closes the cursor after usage
        print("Execute Read")
        with self.connection.cursor() as cur:
            cur.execute(query)
            return pd.DataFrame(cur.fetchall())


if __name__ == "__main__":
    print("works")
    df = london_energy_api()
    df = df.rename(columns={"pes_id": "customer_id", "datetime_gmt": "timestamp", "generation_mw":"pv_output"})
    d = DB_Connector()
    print(d.read("SELECT * FROM app.customers;"))
    print(d.read("SELECT * FROM app.pvlog;"))
    d.write(df, "app.pvlog")
    print(d.read("SELECT * FROM app.pvlog;"))
