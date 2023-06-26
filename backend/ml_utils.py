import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pickle
from backend.db_utils import DB_Connector
from backend.api_utils import Weather_API


def train_model(eval: bool = False):
    """train_model Trains the Linear Regression Model for the SolAI service

    Args:
        eval (bool, optional): Defines if we want to evaluate the model after
        training. Defaults to False.
    """

    # We just take one independend variable here. The normal irradiance instant
    # shows the highest correlation score and is sufficient for a first MVP
    df = _create_training_data()
    x = df["direct_normal_irradiance_instant"].to_numpy().reshape(-1, 1)
    y = df["generation_mw"].to_numpy().reshape(-1, 1)

    # creating train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=21
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    # saving the model to disk
    pickle.dump(model, open("trained_model.pickle", "wb"))

    if eval:
        _eval_model(model, X_test, y_test)


def predict(user_id: int) -> pd.DataFrame:
    """predict uses the trained_model to predict for a specific user_id

    Args:
        user_id (int): unique user identifier

    Returns:
        pd.DataFrame: resulting DataFrame that contains the predicted time,
        the weather forecasts and the predicted pv output
    """
    w = Weather_API(user_id)
    data = w.get()
    time = data["time"]

    x = data["direct_normal_irradiance_instant"].to_numpy().reshape(-1, 1)

    model = pickle.load(open("trained_model.pickle", "rb"))
    pred = model.predict(x)

    df = pd.DataFrame(time, columns=["time"]).set_index("time")
    df["forecast"] = x
    df["pred"] = pred

    return df


def _create_training_data() -> pd.DataFrame:
    """_create_training_data Helper function to read in the database content
    and prepare them for training.

    Returns:
        pd.DataFrame: merged Dataframe
    """

    db = DB_Connector()

    forecasts_data = db.read_to_df("SELECT * from app.forecasts;")

    pv_data = db.read_to_df("SELECT * from app.pvlog;")
    pv_data = pv_data.drop(columns=["pes_id"])

    merged_data = pd.merge(
        forecasts_data,
        pv_data,
        left_on=["time", "customer_id"],
        right_on=["datetime_gmt", "customer_id"],
        how="inner",
    )
    merged_data = merged_data[["direct_normal_irradiance_instant",
                               "generation_mw"]]
    return merged_data


def _eval_model(model, X_test, y_test):
    """_eval_model Performs a Mean Squared Error Evaluation for the given model

    Args:
        model (_type_): given model that needs to contain a .predict method
        X_test (_type_): numpy array with dimensions (n,m).
        Where m is the number of independent variables the model was trained on
        y_test (_type_): numpy array with dimensions(n,m)
    """
    predictions = model.predict(X_test)
    # Evaluate the model
    print("Mean Squared Error", mean_squared_error(y_test, predictions))
    # print("Mean Absolute Error", mean_absolute_error(y_test, predictions))
    print("Model Coefs", model.coef_)
