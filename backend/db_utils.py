import pandas as pd
import psycopg2
import psycopg2.extras as extras


class DB_Connector:
    """DB_Connector offers helper methods to connect, write and read from the
    local database
    """

    def __init__(self):
        """__init__ The connection parameters are hardcoded and only work
        in relation with the pgdb docker container
        """

        # Connection has to be closes manually at the end connection.close()
        self.connection = psycopg2.connect(
            host="pgdb",
            port="5432",
            database="postgres",
            user="postgres",
            password="postgres",
        )

    def write_df(self, df: pd.DataFrame, table: str) -> None:
        """write_df Using psycopg2.extras.execute_values() to insert the
        dataframe.
        It's important that the columsn in the given pandas DataFrame have the
        same names like the database table
        Reference:
        https://naysan.ca/2020/05/09/pandas-to-postgresql-
        using-psycopg2-bulk-insert-performance-benchmark/


        Args:
            df (pd.DataFrame): DataFrame we want to write to the database
            table (str): Name of the database table -> app.forecasts

        Returns:
            _type_: Only returns exception if connection fails
        """

        # Create a list of tupples from the dataframe values
        tuples = [tuple(x) for x in df.to_numpy()]
        # Comma-separated dataframe columns
        cols = ",".join(list(df.columns))
        # SQL quert to execute
        query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
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

    def query(self, query: str) -> str:
        """query let's us use all DB queries and returns them as a string

        Args:
            query (str): Postgres SQL Query we want to execute

        Returns:
            str: Returns the string output of the SQL query
        """

        with self.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def read_to_df(self, query: str) -> pd.DataFrame:
        """read_to_df Stores the result of a SQL query into a pandas DataFrame
        The first column will be used as index column. Will error out, if the
        result is empty

        Args:
            query (str): Postgres SQL Query we want to execute

        Returns:
            pd.DataFrame: The resulting pandas DataFrame
        """

        # Will throw an error if the chosen table is empty
        # closes the cursor after usage
        with self.connection.cursor() as cur:
            cur.execute(query)
            df = pd.DataFrame(cur.fetchall())
            cols = [c[0] for c in cur.description]
            df.columns = cols
            df = df.set_index(df.columns[0])
            return df

    def check_table_for_content(self, table: str) -> bool:
        """check_table_for_content Checks if the table exists and has at least
        one entry
            table:str = the name of the table we want to check
        Args:
            table (str): Name of the database table -> app.forecasts

        Returns:
            bool: returns True if the table contains something
        """
        with self.connection.cursor() as cur:
            cur.execute(f"SELECT EXISTS(SELECT * FROM {table} LIMIT 1)")
            return cur.fetchall()[0][0]
