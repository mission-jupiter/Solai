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
from backend.api_utils import Weather_API




def train_model(eval:bool = False):

    df =  _create_training_data()
    x = df["direct_normal_irradiance_instant"].to_numpy().reshape(-1,1)
    y = df["generation_mw"].to_numpy().reshape(-1,1)

    # creating train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=21)
    
    model = LinearRegression()
    model.fit(X_train, y_train)

    # saving the model to disk
    pickle.dump(model, open("trained_model.pickle", "wb"))

    if eval:
        _eval_model(model, X_test, y_test)


def predict(user_id:int) -> pd.DataFrame:
    w = Weather_API(user_id)
    data = w.get()
    time = data["time"]

    x = data["direct_normal_irradiance_instant"].to_numpy().reshape(-1,1)
    
    model = pickle.load(open("trained_model.pickle", "rb"))
    pred = model.predict(x)

    df = pd.DataFrame(time, columns=["time"]).set_index("time")
    df["forecast"] = x
    df["pred"] = pred
    
    return df


def _create_training_data() -> pd.DataFrame:
    '''
    This function is used to create the training and testings data for the
    ML model
    '''
    db = DB_Connector()

    forecasts_data = db.read_to_df("SELECT * from app.forecasts;")
    
    pv_data = db.read_to_df("SELECT * from app.pvlog;")
    pv_data = pv_data.drop(columns=["pes_id"])

    merged_data = pd.merge(forecasts_data, pv_data, left_on=["time","customer_id"], right_on=["datetime_gmt", "customer_id"], how="inner")
    merged_data = merged_data[["direct_normal_irradiance_instant", "generation_mw"]]
    return merged_data

def _eval_model(model, X_test, y_test):
    predictions = model.predict(X_test)
    # Evaluate the model
    # model evaluation
    print("Mean Squared Error", mean_squared_error(y_test, predictions))
    #print("Mean Absolute Error", mean_absolute_error(y_test, predictions))
    print("Model Coefs", model.coef_)