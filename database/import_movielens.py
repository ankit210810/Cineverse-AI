
import csv
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw" / "ml-100k"
DB_PATH = PROJECT_DIR / "database" / "cineverse.db"


def import_movielens():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Import genre names
        genres = {}

        with open(DATA_DIR / "u.genre", encoding="latin-1") as file:
            for row in csv.reader(file, delimiter="|"):
                if len(row) >= 2 and row[1].strip():
                    genres[int(row[1])] = row[0]

        # Import movies
        movie_count = 0

        with open(DATA_DIR / "u.item", encoding="latin-1") as file:
            reader = csv.reader(file, delimiter="|")

            for row in reader:
                if len(row) < 24:
                    continue

                movie_id = int(row[0])
                title = row[1]
                release_date = row[2]

                year = None
                if release_date:
                    try:
                        year = int(release_date[-4:])
                    except ValueError:
                        pass

                movie_genres = [
                    genres[i]
                    for i, flag in enumerate(row[5:24])
                    if flag == "1" and i in genres
                ]

                cursor.execute("""
                    INSERT OR REPLACE INTO movies
                    (movie_id, title, release_year, genres)
                    VALUES (?, ?, ?, ?)
                """, (
                    movie_id,
                    title,
                    year,
                    ", ".join(movie_genres)
                ))

                movie_count += 1

        # Import MovieLens sample users
        user_ids = set()

        with open(DATA_DIR / "u.data", encoding="latin-1") as file:
            reader = csv.reader(file, delimiter="\t")

            for row in reader:
                if len(row) == 4:
                    user_ids.add(int(row[0]))

        for user_id in sorted(user_ids):
            cursor.execute("""
                INSERT OR IGNORE INTO users
                (user_id, username, display_name, user_type)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                f"movielens_user_{user_id}",
                f"MovieLens User {user_id}",
                "movielens"
            ))

        # Import ratings
        rating_count = 0

        with open(DATA_DIR / "u.data", encoding="latin-1") as file:
            reader = csv.reader(file, delimiter="\t")

            for row in reader:
                if len(row) != 4:
                    continue

                user_id, movie_id, rating, timestamp = row

                rated_at = datetime.fromtimestamp(
                    int(timestamp), timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    INSERT OR REPLACE INTO ratings
                    (user_id, movie_id, rating, rated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    int(user_id),
                    int(movie_id),
                    float(rating),
                    rated_at
                ))

                rating_count += 1

        connection.commit()

        print("\nCineverse MovieLens import completed!")
        print(f"Movies imported: {movie_count}")
        print(f"Users imported: {len(user_ids)}")
        print(f"Ratings imported: {rating_count}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    import_movielens()
