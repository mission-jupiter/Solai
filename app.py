import pandas as pd
import numpy as np
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression
from backend.api_utils import Weather_API, PV_API
from backend.init_db import DB_Initializer
from backend.ml_utils import train_model, predict


if __name__=="__main__":

    dbinit = DB_Initializer()
    dbinit.init()

    #train_model(eval=True)