import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "cineverse.db"


def get_popular_movies(
    limit: int = 10,
    user_id: Optional[int] = None,
    genre: Optional[str] = None
) -> List[Tuple[Any, ...]]:
    """Get popular movies using Bayesian weighted average ratings.
    
    If user_id is provided, movies already rated by the user are excluded.
    """
    connection = sqlite3.connect(DB_PATH)

    try:
        where_clauses = ["1=1"]
        params: List[Any] = []

        if user_id is not None:
            where_clauses.append("m.movie_id NOT IN (SELECT movie_id FROM ratings WHERE user_id = ?)")
            params.append(user_id)

        if genre is not None and genre.strip():
            where_clauses.append("m.genres LIKE ?")
            params.append(f"%{genre.strip()}%")

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                AVG(r.rating) AS average_rating,
                (
                    (COUNT(r.rating_id) * AVG(r.rating) +
                    50 * (SELECT AVG(rating) FROM ratings))
                    /
                    (COUNT(r.rating_id) + 50)
                ) AS weighted_rating
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            WHERE {where_sql}
            GROUP BY m.movie_id
            HAVING COUNT(r.rating_id) >= 20
            ORDER BY weighted_rating DESC
            LIMIT ?
        """

        return connection.execute(query, params).fetchall()

    finally:
        connection.close()


if __name__ == "__main__":
    movies = get_popular_movies()

    print("\n===== CINEVERSE WEIGHTED POPULARITY =====\n")

    for index, movie in enumerate(movies, start=1):
        movie_id, title, year, genres, count, rating, weighted = movie

        print(f"{index}. {title}")
        print(f"   Average rating: {rating:.2f}/5")
        print(f"   Ratings: {count}")
        print(f"   Weighted score: {weighted:.3f}")
        print()
