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
    # En production sur Render, utiliser DATABASE_URL.
    # En local, utiliser les variables DB_* du fichier .env.
    if DATABASE_URL and os.getenv("ENVIRONMENT") == "production":
        return psycopg.connect(DATABASE_URL)

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