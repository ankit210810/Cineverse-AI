"""Feedback Service for Cineverse AI.

Handles user ratings, watchlist management, and recommendation feedback (likes/dislikes).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from database.db import get_db_connection


# ---------------------------------------------------------
# RATINGS
# ---------------------------------------------------------

def rate_movie(user_id: int, movie_id: int, rating: float) -> bool:
    """Record or update a movie rating (0.5 to 5.0)."""
    rating = max(0.5, min(5.0, float(rating)))
    rated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO ratings (user_id, movie_id, rating, rated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                rating = excluded.rating,
                rated_at = excluded.rated_at
        """, (user_id, movie_id, rating, rated_at))

        conn.commit()
        return True
    finally:
        conn.close()


def get_user_rating(user_id: int, movie_id: int) -> Optional[float]:
    """Get the specific rating a user gave to a movie, if any."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT rating FROM ratings WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        ).fetchone()
        return float(row["rating"]) if row else None
    finally:
        conn.close()


def get_user_ratings(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieve all movies rated by a specific user."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT 
                r.rating_id,
                r.user_id,
                r.movie_id,
                r.rating,
                r.rated_at,
                m.title,
                m.release_year,
                m.genres
            FROM ratings r
            JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = ?
            ORDER BY r.rated_at DESC, r.rating_id DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset)).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            results.append(d)
        return results
    finally:
        conn.close()


def delete_rating(user_id: int, movie_id: int) -> bool:
    """Delete a user's rating for a movie."""
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM ratings WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ---------------------------------------------------------
# WATCHLIST
# ---------------------------------------------------------

def add_to_watchlist(user_id: int, movie_id: int) -> bool:
    """Add a movie to user's personal watchlist."""
    added_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO watchlist (user_id, movie_id, added_at)
            VALUES (?, ?, ?)
        """, (user_id, movie_id, added_at))
        conn.commit()
        return True
    finally:
        conn.close()


def remove_from_watchlist(user_id: int, movie_id: int) -> bool:
    """Remove a movie from user's watchlist."""
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def is_in_watchlist(user_id: int, movie_id: int) -> bool:
    """Check if movie is present in user's watchlist."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def get_watchlist(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve full details of all movies in user's watchlist."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT 
                w.watchlist_id,
                w.user_id,
                w.movie_id,
                w.added_at,
                m.title,
                m.release_year,
                m.genres,
                COUNT(r.rating_id) AS rating_count,
                COALESCE(AVG(r.rating), 0.0) AS avg_rating
            FROM watchlist w
            JOIN movies m ON w.movie_id = m.movie_id
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE w.user_id = ?
            GROUP BY m.movie_id
            ORDER BY w.added_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["avg_rating"] = round(d["avg_rating"], 2)
            d["genres_list"] = [g.strip() for g in d["genres"].split(",") if g.strip()] if d["genres"] else []
            results.append(d)
        return results
    finally:
        conn.close()


# ---------------------------------------------------------
# FEEDBACK (LIKE / DISLIKE)
# ---------------------------------------------------------

def set_feedback(user_id: int, movie_id: int, feedback_type: str) -> bool:
    """Record like or dislike feedback for a recommendation."""
    if feedback_type not in ("like", "dislike"):
        raise ValueError("feedback_type must be 'like' or 'dislike'")

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO feedback (user_id, movie_id, feedback_type, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                feedback_type = excluded.feedback_type,
                created_at = excluded.created_at
        """, (user_id, movie_id, feedback_type, created_at))
        conn.commit()
        return True
    finally:
        conn.close()


def remove_feedback(user_id: int, movie_id: int) -> bool:
    """Clear like or dislike feedback for a movie."""
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM feedback WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_feedback(user_id: int, movie_id: int) -> Optional[str]:
    """Get active feedback ('like' | 'dislike') for a movie."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT feedback_type FROM feedback WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        ).fetchone()
        return row["feedback_type"] if row else None
    finally:
        conn.close()


def get_user_feedback_map(user_id: int) -> Dict[int, str]:
    """Retrieve all feedback by user as a movie_id -> type dictionary."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT movie_id, feedback_type FROM feedback WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return {r["movie_id"]: r["feedback_type"] for r in rows}
    finally:
        conn.close()
