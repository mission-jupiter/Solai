import requests
import pydantic
from datetime import datetime, timedelta
from typing import Literal,List,Union
import pandas as pd
import io
import psycopg2
import psycopg2.extras as extras
from io import StringIO

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

# TODO: Next step. Write a class that connects to db and can do stuff for us
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
        

    def write_dataframe(self, df):
        df.to_sql('app.pv_log', self.connection, if_exists='replace', index=False)
    

    # https://naysan.ca/2020/05/09/pandas-to-postgresql-using-psycopg2-bulk-insert-performance-benchmark/
    def execute_values(self, df, table):
        """
        Using psycopg2.extras.execute_values() to insert the dataframe
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



    def read(self, query:str):
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
    d.execute_values(df, "app.pvlog")
    print(d.read("SELECT * FROM app.pvlog;"))
