from glob import glob
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from backend.db_utils import DB_Connector
from pydantic import BaseModel
from backend.api_utils import PV_API


class DB_Initializer(BaseModel):

    def init(self):
        db = DB_Connector()
        if ((db.check_table_for_content("app.forecasts") == False) & (db.check_table_for_content("app.pvlog") == False)):
            self._write_forecasts_to_db()
            self._write_pv_data_to_db()
            print("Database initialized")
        else:
            print("Tables are already initialized")

    def _write_forecasts_to_db(self) -> pd.DataFrame:
        
        def df_generator() -> pd.DataFrame:
            path = "./weather_forecasts/"
            for user in os.listdir(path):
                for file in glob(os.path.join(path, user, "*.csv")):
                    df = pd.read_csv(file, index_col=None)
                    yield df
                       
        df = pd.concat(df_generator(), ignore_index=True)

        '''
        Now we filter out duplicates of the time column
        Why? If someone calls the API often the jsons will contain vaguely
        the same forecasts
        '''
        df = df.drop_duplicates(subset="time")

        # Now we can load the data into the database
        db = DB_Connector()
        db.write_df(df, "app.forecasts")
        return(db.read_to_df("SELECT * FROM app.forecasts limit 10").head(10))
    
    def _write_pv_data_to_db(self) -> pd.DataFrame:
        pv = PV_API(1)
        db = DB_Connector()
        df = pv.get()
        db.write_df(df, "app.pvlog")
        return(db.read_to_df("SELECT * FROM app.pvlog limit 10").head(10))
