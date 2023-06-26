from backend.init_db import DB_Initializer
from backend.ml_utils import train_model


if __name__ == "__main__":
    # First we initialize and populate the database
    dbinit = DB_Initializer()
    dbinit.init()
    # Now we train our Regression Model
    train_model(eval=True)
