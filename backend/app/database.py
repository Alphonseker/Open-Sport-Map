from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

DB_CONFIG = {
    "dbname": "open_sport_map",
    "user": "spotter",
    "password": "spotter_password",
    "host": "localhost",
    "port": 5433
}

@contextmanager
def get_db_cursor():
    """Context manager ensuring clean connection and cursor lifecycle."""
    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()