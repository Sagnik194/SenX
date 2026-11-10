
import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "senx_db")
DB_USER = os.getenv("DB_USER", "senx_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Safely construct the database URL.
# This handles special characters in passwords.
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={"charset": "utf8mb4"}
)
