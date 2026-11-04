
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cineverse.db"

connection = sqlite3.connect(DB_PATH)

print("\n===== CINEVERSE DATABASE REPORT =====\n")

for table in ["users", "movies", "ratings"]:
    count = connection.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table.capitalize()}: {count:,}")

print("\n===== SAMPLE MOVIES =====\n")

movies = connection.execute("""
    SELECT movie_id, title, release_year, genres
    FROM movies
    ORDER BY movie_id
    LIMIT 5
""").fetchall()

for movie in movies:
    print(movie)

connection.close()
print("\nDatabase verification completed!")
