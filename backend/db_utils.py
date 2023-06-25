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


# Database Connectors
class DB_Connector():
    def __init__(self):
        # Connection has to be closes manually at the end connection.close()
        self.connection = psycopg2.connect(
                host="pgdb",
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
        Always take the whole dataframe or at least the primary key with it,
        because the first column will be taken as index of the DataFrame

        Will throw an error if the chosen table is empty
        '''
        # closes the cursor after usage
        with self.connection.cursor() as cur:
            cur.execute(query)
            df = pd.DataFrame(cur.fetchall())
            cols = [c[0] for c in cur.description]
            df.columns = cols
            df = df.set_index(df.columns[0])
            return df
        
    def check_table_for_content(self, table:str) -> bool:
        '''
            Checks if the table exists and has at least one entry
            table:str = the name of the table we want to check
        '''
        with self.connection.cursor() as cur:
            cur.execute(f"SELECT EXISTS(SELECT * FROM {table} LIMIT 1)")
            return cur.fetchall()[0][0]