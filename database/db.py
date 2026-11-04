import sqlite3
from pathlib import Path

# Find the Cineverse project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Database and schema locations
DATABASE_PATH = PROJECT_DIR / "database" / "cineverse.db"
SCHEMA_PATH = PROJECT_DIR / "database" / "schema.sql"


def get_db_connection():
    """Create and return a thread-safe configured database connection."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the Cineverse database and its tables."""

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        connection.commit()

        print("Cineverse database created successfully!")
        print(f"Database location: {DATABASE_PATH}")

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """).fetchall()

        print("\nDatabase tables:")
        for table in tables:
            print(f"- {table[0]}")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
