import os
import psycopg2
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

try:
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    print("================================")
    print("DATABASE CONNECTION SUCCESSFUL")
    print("================================")

    connection.close()

except Exception as error:
    print("================================")
    print("DATABASE CONNECTION FAILED")
    print("================================")
    print(error)