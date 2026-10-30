
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telemed_secure")


def get_connection():
    if DATABASE_URL:
        conn = psycopg.connect(DATABASE_URL)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    current_database(),
                    current_schema(),
                    current_setting('search_path'),
                    to_regclass('public.utilisateurs')
            """)
            print("DIAGNOSTIC BASE :", cur.fetchone())

        return conn

    if not DB_USER:
        raise RuntimeError("DB_USER absente du fichier .env")

    if not DB_PASSWORD:
        raise RuntimeError("DB_PASSWORD absente du fichier .env")

    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
