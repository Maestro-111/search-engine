import psycopg2
from psycopg2 import sql

# import pandas as pd
# import numpy as np


def fetch_train_data(
    table_name,
    host="localhost",
    port=6001,
    dbname="your_db",
    user="your_user",
    password="your_password",
):
    """
    to do
    """

    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password
        )

        cursor = conn.cursor()

        # Use SQL composition to prevent SQL injection
        query = sql.SQL(f"SELECT * FROM {table_name} LIMIT 5").format(
            sql.Identifier(table_name)
        )
        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()
        return rows

    except Exception as e:
        print("Error:", e)
        return []


rows = fetch_train_data(
    "user_trainingdata",
    host="db",
    port=5432,
    dbname="search_db",
    user="search_admin",
    password="1234",
)

print(rows)
