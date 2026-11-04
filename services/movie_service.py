"""Movie Service for Cineverse AI.

Provides movie retrieval, search, multi-genre filtering, mood-based discovery,
top-rated and trending catalogs, and content-similarity matching.
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from database.db import get_db_connection

# Comprehensive mood mapping based on cinematic emotional tones
MOOD_GENRE_MAP: Dict[str, Dict[str, Any]] = {
    "Happy": {
        "genres": ["Comedy", "Animation", "Musical"],
        "tagline": "Feel-good laughs, vibrant animation, and uplifting joy.",
        "badge": "☀️ Pure Joy"
    },
    "Sad": {
        "genres": ["Drama", "War"],
        "tagline": "Deeply emotional, poignant, and touching human stories.",
        "badge": "🌧️ Deep Emotion"
    },
    "Romantic": {
        "genres": ["Romance", "Comedy", "Drama"],
        "tagline": "Passionate encounters, heartfelt love, and romance.",
        "badge": "💖 Heartfelt & Warm"
    },
    "Suspenseful": {
        "genres": ["Thriller", "Mystery", "Crime", "Film-Noir"],
        "tagline": "High-stakes tension, dark secrets, and edge-of-seat thrills.",
        "badge": "⚡ Edge of Seat"
    },
    "Adventurous": {
        "genres": ["Adventure", "Action", "Sci-Fi"],
        "tagline": "Epic journeys, daring quests, and heart-pumping spectacle.",
        "badge": "🧭 Epic Quests"
    },
    "Inspirational": {
        "genres": ["Drama", "Documentary", "War"],
        "tagline": "Triumphs of the human spirit, courage, and perseverance.",
        "badge": "✨ Inspiring Triumph"
    },
    "Mind-bending": {
        "genres": ["Sci-Fi", "Mystery", "Thriller"],
        "tagline": "Twisting realities, philosophical puzzles, and genius plot twists.",
        "badge": "🌀 Reality Twisting"
    },
    "Relaxed": {
        "genres": ["Animation", "Comedy", "Adventure"],
        "tagline": "Easygoing comfort cinema to unwind after a long day.",
        "badge": "🛋️ Chill & Unwind"
    }
}


def get_movie(movie_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve movie details along with aggregate rating metrics."""
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT 
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                COALESCE(AVG(r.rating), 0.0) AS avg_rating
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE m.movie_id = ?
            GROUP BY m.movie_id
        """, (movie_id,)).fetchone()
        
        if not row:
            return None
            
        data = dict(row)
        data["avg_rating"] = round(data["avg_rating"], 2)
        data["genres_list"] = [g.strip() for g in data["genres"].split(",") if g.strip()] if data["genres"] else []
        return data
    finally:
        conn.close()


def get_movies_by_ids(movie_ids: List[int]) -> List[Dict[str, Any]]:
    """Retrieve multiple movies in the specific order requested."""
    if not movie_ids:
        return []
        
    conn = get_db_connection()
    try:
        placeholders = ",".join("?" for _ in movie_ids)
        rows = conn.execute(f"""
            SELECT 
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                COALESCE(AVG(r.rating), 0.0) AS avg_rating
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE m.movie_id IN ({placeholders})
            GROUP BY m.movie_id
        """, movie_ids).fetchall()
        
        row_map = {}
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            row_map[d["movie_id"]] = d
            
        return [row_map[mid] for mid in movie_ids if mid in row_map]
    finally:
        conn.close()


def get_all_genres() -> List[str]:
    """Return all distinct genre names in alphabetical order."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT genres FROM movies WHERE genres IS NOT NULL").fetchall()
        genres_set = set()
        for r in rows:
            if r["genres"]:
                for g in r["genres"].split(","):
                    clean = g.strip()
                    if clean and clean.lower() != "unknown":
                        genres_set.add(clean)
        return sorted(list(genres_set))
    finally:
        conn.close()


def search_movies(
    query: Optional[str] = None,
    genres: Optional[List[str]] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    rating_min: Optional[float] = None,
    sort_by: str = "popularity",
    limit: int = 24,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Search and filter movies with pagination and accurate aggregate counting."""
    conn = get_db_connection()
    try:
        where_clauses = ["1=1"]
        params: List[Any] = []

        if query and query.strip():
            where_clauses.append("m.title LIKE ?")
            params.append(f"%{query.strip()}%")

        if year_min is not None:
            where_clauses.append("m.release_year >= ?")
            params.append(year_min)

        if year_max is not None:
            where_clauses.append("m.release_year <= ?")
            params.append(year_max)

        if genres:
            for g in genres:
                where_clauses.append("m.genres LIKE ?")
                params.append(f"%{g}%")

        where_sql = " AND ".join(where_clauses)

        having_clause = ""
        having_params: List[Any] = []
        if rating_min is not None and rating_min > 0:
            having_clause = "HAVING avg_rating >= ?"
            having_params.append(rating_min)

        # Ordering logic
        if sort_by == "rating":
            order_sql = "ORDER BY avg_rating DESC, rating_count DESC"
        elif sort_by == "year_desc":
            order_sql = "ORDER BY m.release_year DESC NULLS LAST, rating_count DESC"
        elif sort_by == "year_asc":
            order_sql = "ORDER BY m.release_year ASC NULLS LAST, rating_count DESC"
        elif sort_by == "title":
            order_sql = "ORDER BY m.title ASC"
        else:  # popularity (weighted rating default)
            order_sql = "ORDER BY rating_count DESC, avg_rating DESC"

        query_sql = f"""
            SELECT 
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                COALESCE(AVG(r.rating), 0.0) AS avg_rating
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE {where_sql}
            GROUP BY m.movie_id
            {having_clause}
            {order_sql}
            LIMIT ? OFFSET ?
        """

        full_params = params + having_params + [limit, offset]
        rows = conn.execute(query_sql, full_params).fetchall()

        # Count total matching
        count_sql = f"""
            SELECT COUNT(*) FROM (
                SELECT m.movie_id, COALESCE(AVG(r.rating), 0.0) AS avg_rating
                FROM movies m
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE {where_sql}
                GROUP BY m.movie_id
                {having_clause}
            )
        """
        total_count = conn.execute(count_sql, params + having_params).fetchone()[0]

        results = []
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            results.append(d)

        return results, total_count
    finally:
        conn.close()


def get_trending_movies(limit: int = 12) -> List[Dict[str, Any]]:
    """Return top trending movies using Bayesian weighted ranking."""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                AVG(r.rating) AS avg_rating,
                (
                    (COUNT(r.rating_id) * AVG(r.rating) +
                    50 * (SELECT AVG(rating) FROM ratings))
                    /
                    (COUNT(r.rating_id) + 50)
                ) AS score
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id
            HAVING COUNT(r.rating_id) >= 25
            ORDER BY score DESC
            LIMIT ?
        """
        rows = conn.execute(query, (limit,)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["score"] = round(d["score"], 3)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            results.append(d)
        return results
    finally:
        conn.close()


def get_top_rated_movies(limit: int = 12, min_ratings: int = 40) -> List[Dict[str, Any]]:
    """Return top-rated movies meeting a minimum rating threshold."""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                AVG(r.rating) AS avg_rating
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id
            HAVING COUNT(r.rating_id) >= ?
            ORDER BY avg_rating DESC, rating_count DESC
            LIMIT ?
        """
        rows = conn.execute(query, (min_ratings, limit)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            results.append(d)
        return results
    finally:
        conn.close()


def get_mood_movies(mood: str, limit: int = 12) -> List[Dict[str, Any]]:
    """Return top curated movies matching a specific emotional mood."""
    mood_info = MOOD_GENRE_MAP.get(mood)
    if not mood_info:
        return get_trending_movies(limit)

    target_genres = mood_info["genres"]
    genre_likes = " OR ".join(["m.genres LIKE ?" for _ in target_genres])
    params = [f"%{g}%" for g in target_genres] + [limit]

    conn = get_db_connection()
    try:
        query = f"""
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                AVG(r.rating) AS avg_rating,
                (
                    (COUNT(r.rating_id) * AVG(r.rating) + 30 * (SELECT AVG(rating) FROM ratings))
                    / (COUNT(r.rating_id) + 30)
                ) AS score
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            WHERE ({genre_likes})
            GROUP BY m.movie_id
            HAVING COUNT(r.rating_id) >= 15
            ORDER BY score DESC
            LIMIT ?
        """
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["score"] = round(d["score"], 3)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            d["mood_tag"] = mood_info["badge"]
            results.append(d)
        return results
    finally:
        conn.close()


def get_similar_movies(movie_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """Compute content-based genre overlap to recommend similar titles."""
    target = get_movie(movie_id)
    if not target or not target["genres_list"]:
        return []

    target_genres = set(target["genres_list"])
    target_year = target["release_year"] or 1995

    conn = get_db_connection()
    try:
        # Find candidates sharing at least one genre
        placeholders = " OR ".join(["genres LIKE ?" for _ in target_genres])
        params = [f"%{g}%" for g in target_genres] + [movie_id]
        
        query = f"""
            SELECT m.movie_id, m.title, m.release_year, m.genres,
                   COUNT(r.rating_id) AS rating_count,
                   COALESCE(AVG(r.rating), 0.0) AS avg_rating
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE ({placeholders}) AND m.movie_id != ?
            GROUP BY m.movie_id
            HAVING COUNT(r.rating_id) >= 5 OR m.movie_id = 9999 OR m.release_year >= 2020
        """
        rows = conn.execute(query, params).fetchall()
        
        scored = []
        for r in rows:
            d = dict(r)
            m_genres = set(g.strip() for g in d["genres"].split(",") if g.strip()) if d["genres"] else set()
            jaccard = len(target_genres.intersection(m_genres)) / float(len(target_genres.union(m_genres)))
            
            # Era proximity bonus
            year_diff = abs((d["release_year"] or 1995) - target_year)
            era_bonus = max(0.0, 1.0 - (year_diff / 40.0)) * 0.2
            
            score = jaccard * 0.8 + era_bonus + (d["avg_rating"] / 25.0)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["similarity_score"] = round(score, 3)
            d["genres_list"] = list(m_genres)
            scored.append(d)
            
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]
    finally:
        conn.close()
