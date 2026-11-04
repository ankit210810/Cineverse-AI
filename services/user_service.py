"""User Service for Cineverse AI.

Handles user retrieval, creation, taste profile generation, and activity stats.
"""

from typing import Dict, List, Optional, Any
import streamlit as st
from database.db import get_db_connection


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single user by user_id."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT user_id, username, display_name, user_type, created_at FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user by their unique username."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT user_id, username, display_name, user_type, created_at FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_users(limit: int = 50, user_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List users with optional filtering by user_type ('movielens' or 'app')."""
    conn = get_db_connection()
    try:
        if user_type:
            rows = conn.execute(
                "SELECT user_id, username, display_name, user_type, created_at FROM users WHERE user_type = ? ORDER BY user_id LIMIT ?",
                (user_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT user_id, username, display_name, user_type, created_at FROM users ORDER BY user_id LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_demo_users() -> List[Dict[str, Any]]:
    """Return a curated set of users for easy persona switching in the UI."""
    conn = get_db_connection()
    try:
        # Predefined varied personas + any app-created users
        featured_ids = [42, 1, 13, 276, 405, 655]
        placeholders = ",".join("?" for _ in featured_ids)
        rows = conn.execute(
            f"SELECT user_id, username, display_name, user_type, created_at FROM users WHERE user_id IN ({placeholders})",
            featured_ids
        ).fetchall()
        
        # Also grab any newly created app users
        app_rows = conn.execute(
            "SELECT user_id, username, display_name, user_type, created_at FROM users WHERE user_type = 'app' ORDER BY user_id DESC LIMIT 5"
        ).fetchall()
        
        combined = {r["user_id"]: dict(r) for r in rows}
        for r in app_rows:
            combined[r["user_id"]] = dict(r)
        
        return list(combined.values())
    finally:
        conn.close()


def create_user(username: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new Cineverse user."""
    conn = get_db_connection()
    try:
        display = display_name or username.replace("_", " ").title()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, display_name, user_type) VALUES (?, ?, 'app')",
            (username.strip(), display.strip())
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "user_id": user_id,
            "username": username.strip(),
            "display_name": display.strip(),
            "user_type": "app"
        }
    finally:
        conn.close()


@st.cache_data(ttl=3600, show_spinner=False)
def ensure_admin_user(email: str = "ankitkumar2009ara@gmail.com", display_name: str = "Ankit Kumar") -> Dict[str, Any]:
    """Ensures the primary admin user exists in the database with administrator privileges."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT user_id, username, display_name, user_type, created_at FROM users WHERE username = ? OR username = 'ankit'",
            (email,)
        ).fetchone()
        if row:
            uid = row["user_id"]
            if row["user_type"] != "admin" or row["display_name"] != display_name:
                conn.execute(
                    "UPDATE users SET user_type = 'admin', display_name = ? WHERE user_id = ?",
                    (display_name, uid)
                )
                conn.commit()
            return {
                "user_id": uid,
                "username": email,
                "display_name": display_name,
                "user_type": "admin",
                "email": email,
                "is_admin": True
            }

        # Create the admin user
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, display_name, user_type) VALUES (?, ?, 'admin')",
            (email, display_name)
        )
        conn.commit()
        uid = cursor.lastrowid

        # Seed curated watch history and ratings for Ankit
        curated_movies = [
            (10003, 5.0), # Interstellar
            (10001, 5.0), # Inception
            (10002, 4.5), # The Matrix
            (10006, 4.5), # Dune
            (10004, 4.5), # Arrival
            (313, 4.0),   # Titanic
            (50, 4.5),    # Star Wars
            (56, 4.5),    # Pulp Fiction
            (89, 4.5),    # Blade Runner
            (96, 4.5),    # Terminator 2
            (127, 5.0),   # The Godfather
            (174, 4.5),   # Raiders of the Lost Ark
        ]
        for mid, r in curated_movies:
            conn.execute(
                "INSERT OR IGNORE INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)",
                (uid, mid, r)
            )
            conn.execute(
                "INSERT OR IGNORE INTO watch_history (user_id, movie_id) VALUES (?, ?)",
                (uid, mid)
            )
        conn.commit()
        return {
            "user_id": uid,
            "username": email,
            "display_name": display_name,
            "user_type": "admin",
            "email": email,
            "is_admin": True
        }
    finally:
        conn.close()


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Calculate activity statistics for a user."""
    conn = get_db_connection()
    try:
        ratings_stat = conn.execute(
            "SELECT COUNT(*) as cnt, AVG(rating) as avg_rating FROM ratings WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        watchlist_cnt = conn.execute(
            "SELECT COUNT(*) as cnt FROM watchlist WHERE user_id = ?",
            (user_id,)
        ).fetchone()["cnt"]
        
        history_cnt = conn.execute(
            "SELECT COUNT(*) as cnt FROM watch_history WHERE user_id = ?",
            (user_id,)
        ).fetchone()["cnt"]
        
        feedback_stat = conn.execute(
            "SELECT feedback_type, COUNT(*) as cnt FROM feedback WHERE user_id = ? GROUP BY feedback_type",
            (user_id,)
        ).fetchall()
        feedback_map = {row["feedback_type"]: row["cnt"] for row in feedback_stat}

        return {
            "ratings_count": ratings_stat["cnt"] or 0,
            "average_rating": round(ratings_stat["avg_rating"], 2) if ratings_stat["avg_rating"] else 0.0,
            "watchlist_count": watchlist_cnt,
            "history_count": history_cnt,
            "likes_count": feedback_map.get("like", 0),
            "dislikes_count": feedback_map.get("dislike", 0)
        }
    finally:
        conn.close()


def get_user_taste_profile(user_id: int) -> Dict[str, Any]:
    """Analyze ratings and history to build a multi-dimensional taste profile."""
    conn = get_db_connection()
    try:
        # Fetch movies rated by user with rating >= 3.0 (positive preference)
        rows = conn.execute("""
            SELECT r.rating, m.genres, m.release_year
            FROM ratings r
            JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = ?
        """, (user_id,)).fetchall()

        if not rows:
            return {
                "top_genres": [],
                "genre_distribution": {},
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "total_rated": 0,
                "favorite_era": "No data",
                "taste_summary": "New Cineverse Explorer. Watch and rate movies to generate your personalized taste profile."
            }

        genre_counts: Dict[str, int] = {}
        genre_weighted: Dict[str, float] = {}
        rating_dist: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        decades: Dict[str, int] = {}

        for row in rows:
            r = float(row["rating"])
            rounded_r = max(1, min(5, int(round(r))))
            rating_dist[rounded_r] = rating_dist.get(rounded_r, 0) + 1

            if row["genres"]:
                movie_genres = [g.strip() for g in row["genres"].split(",") if g.strip()]
                for g in movie_genres:
                    genre_counts[g] = genre_counts.get(g, 0) + 1
                    genre_weighted[g] = genre_weighted.get(g, 0.0) + r

            year = row["release_year"]
            if year:
                decade = f"{(year // 10) * 10}s"
                decades[decade] = decades.get(decade, 0) + 1

        # Calculate genre average rating and top genres
        genre_profile = []
        for g, count in genre_counts.items():
            avg_r = genre_weighted[g] / count
            genre_profile.append({
                "genre": g,
                "count": count,
                "average_rating": round(avg_r, 2)
            })

        genre_profile.sort(key=lambda x: (x["count"], x["average_rating"]), reverse=True)
        top_genres = [item["genre"] for item in genre_profile[:5]]

        fav_era = max(decades.items(), key=lambda x: x[1])[0] if decades else "Modern Era"

        summary = f"Passionate about {', '.join(top_genres[:3]) if top_genres else 'Cinema'}. Most active in {fav_era} cinema with {len(rows)} verified ratings."

        return {
            "top_genres": top_genres,
            "genre_profile": genre_profile,
            "genre_distribution": genre_counts,
            "rating_distribution": rating_dist,
            "total_rated": len(rows),
            "favorite_era": fav_era,
            "taste_summary": summary
        }
    finally:
        conn.close()


# Re-exports for convenience
try:
    from services.feedback_service import is_in_watchlist, add_to_watchlist, remove_from_watchlist, get_watchlist
except ImportError:
    pass

