import pandas as pd
import numpy as np
import setup.app_utils as au
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression

def test_db():
    db = au.DB_Connector()
    #print(db.query("SELECT schema_name FROM information_schema.schemata;"))
    print(db.read_to_df("Select * from app.forecasts;"))
    #print(db.read_to_df("Select * from app.pvlog;"))

def init_tables():
    au.write_forecasts_to_db(1)
    au.write_pvdata_to_db(1)

if __name__=="__main__":
    #print("test")
    db = au.DB_Connector()

    # Just init DB when tables are empty
    if ((len(db.read_to_df("select * from app.forecasts limit 1;")) != 1) & (len(db.read_to_df("select * from app.pvlog limit 1;")) != 1)):
        init_tables()

    #test_db()
    #init_tables()
    au.train_model()
    print(au.predict(1).head(20))
    #print(au.get_forecast(user_id=1,  write_to_db=False, write_to_json=True))
    #au.write_forecasts_to_db(1)