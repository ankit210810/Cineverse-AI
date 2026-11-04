"""Automated Verification and Test Suite for Cineverse AI.

Tests database connectivity, models, cold-start mechanics, failover fallback,
watchlist, ratings, search, and the AI assistant.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_db_connection
from models.popularity import get_popular_movies
from models.matrix_factorization import MatrixFactorization
from models.transformer import TransformerRecommender
from services.cold_start_service import get_cold_start_engine
from services.model_service import get_model_registry
from services.recommendation_service import get_recommendation_service
from services.movie_service import search_movies, get_movie, get_similar_movies
from services.user_service import get_user, get_user_taste_profile
from services.feedback_service import (
    add_to_watchlist,
    remove_from_watchlist,
    is_in_watchlist,
    get_watchlist,
    rate_movie,
    get_user_rating,
    set_feedback,
    get_feedback,
    remove_feedback
)
from services.assistant_service import get_assistant


class CineverseTestSuite(unittest.TestCase):

    def setUp(self):
        self.test_user_id = 42
        self.unknown_user_id = 999999
        self.test_movie_id = 1  # Toy Story (1995)
        self.cold_movie_id = 9999  # Space Heist 2026

    # 1. Database Connectivity
    def test_01_database_connectivity(self):
        conn = get_db_connection()
        try:
            users_cnt = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            movies_cnt = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
            ratings_cnt = conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]

            self.assertGreater(users_cnt, 900)
            self.assertGreater(movies_cnt, 1600)
            self.assertGreaterEqual(ratings_cnt, 100000)
        finally:
            conn.close()

    # 2. Weighted Popularity Model
    def test_02_popularity_model(self):
        popular = get_popular_movies(limit=10)
        self.assertEqual(len(popular), 10)
        # Verify Bayesian weighted score is positive
        self.assertGreater(popular[0][6], 3.0)

        # Test user exclusion
        pop_user = get_popular_movies(limit=5, user_id=self.test_user_id)
        conn = get_db_connection()
        try:
            rated_by_user = {r[0] for r in conn.execute("SELECT movie_id FROM ratings WHERE user_id = ?", (self.test_user_id,)).fetchall()}
            for m in pop_user:
                self.assertNotIn(m[0], rated_by_user)
        finally:
            conn.close()

    # 3. Matrix Factorization Model
    def test_03_matrix_factorization(self):
        mf = MatrixFactorization()
        loaded = mf.load()
        self.assertTrue(loaded, "Pre-trained MF weights should load successfully.")
        recs = mf.recommend(user_id=self.test_user_id, limit=5)
        self.assertEqual(len(recs), 5)
        # Check that recommended movie tuple has valid title and positive predicted score
        movie_tuple, score = recs[0]
        self.assertIsInstance(movie_tuple, tuple)
        self.assertGreater(len(movie_tuple[1]), 0)  # Title string
        self.assertGreater(score, 0.0)

    # 4. Sequential Transformer Model & Attention
    def test_04_sequential_transformer(self):
        tr = TransformerRecommender()
        loaded = tr.load()
        self.assertTrue(loaded, "Pre-trained Transformer weights should load successfully.")
        recs = tr.recommend(user_id=self.test_user_id, limit=5)
        self.assertEqual(len(recs), 5)

        # Test attention extraction
        att_res = tr.recommend_with_attention(user_id=self.test_user_id, limit=5)
        self.assertIn("attention_weights", att_res)
        self.assertIn("attention_matrix", att_res)
        self.assertGreater(len(att_res["attention_weights"]), 0)
        self.assertAlmostEqual(sum(att_res["attention_weights"]), 1.0, places=2)

    # 5. Cold-Start New Movie ("Space Heist 2026")
    def test_05_cold_start_new_movie(self):
        cold_engine = get_cold_start_engine()
        # Verify Space Heist 2026 exists in features
        self.assertIn(self.cold_movie_id, cold_engine.movie_features)
        feat = cold_engine.movie_features[self.cold_movie_id]
        self.assertTrue(feat["is_cold_start"])
        self.assertEqual(feat["year"], 2026)
        self.assertIn("Sci-Fi", feat["genres"])

        # Recommend for a user with Sci-Fi preferences
        recs = cold_engine.recommend_cold_start(preferred_genres=["Sci-Fi", "Action", "Adventure"], limit=5)
        titles = [r["title"] for r in recs]
        self.assertTrue(any("Space Heist" in t for t in titles))

    # 6. Cold-Start Unknown User & Empty History
    def test_06_cold_start_unknown_user(self):
        rec_service = get_recommendation_service()
        # Recommend for an unknown user ID with 0 ratings
        res = rec_service.get_recommendations(
            user_id=self.unknown_user_id,
            algorithm="Automatic Best Model",
            limit=5
        )
        self.assertIsNotNone(res)
        self.assertGreater(len(res["recommendations"]), 0)

    # 7. Reliability Kill Switch & Automatic Fallback
    def test_07_transformer_kill_and_fallback(self):
        registry = get_model_registry()
        rec_service = get_recommendation_service()

        # Kill the Transformer
        registry.kill_transformer("Test simulated crash")
        status = registry.get_transformer_status()
        self.assertFalse(status["healthy"])
        self.assertEqual(status["status"], "OFFLINE")

        # Request Transformer recommendation
        res = rec_service.get_recommendations(
            user_id=self.test_user_id,
            algorithm="Sequential Transformer",
            limit=5
        )

        # Fallback should be engaged
        self.assertTrue(res["fallback_used"])
        self.assertIn("Fallback", res["algorithm"])
        self.assertEqual(len(res["recommendations"]), 5)

        # Restore Transformer
        registry.restore_transformer()
        restored_status = registry.get_transformer_status()
        self.assertTrue(restored_status["healthy"])

    # 8. Watchlist CRUD Operations
    def test_08_watchlist_operations(self):
        # Clean before test
        remove_from_watchlist(self.test_user_id, self.test_movie_id)
        self.assertFalse(is_in_watchlist(self.test_user_id, self.test_movie_id))

        # Add
        add_to_watchlist(self.test_user_id, self.test_movie_id)
        self.assertTrue(is_in_watchlist(self.test_user_id, self.test_movie_id))

        # List
        wl = get_watchlist(self.test_user_id)
        self.assertTrue(any(item["movie_id"] == self.test_movie_id for item in wl))

        # Remove
        remove_from_watchlist(self.test_user_id, self.test_movie_id)
        self.assertFalse(is_in_watchlist(self.test_user_id, self.test_movie_id))

    # 9. Ratings and Feedback Operations
    def test_09_ratings_and_feedback(self):
        # Rate movie
        rate_movie(self.test_user_id, self.test_movie_id, 4.5)
        rating = get_user_rating(self.test_user_id, self.test_movie_id)
        self.assertEqual(rating, 4.5)

        # Like / Dislike feedback
        set_feedback(self.test_user_id, self.test_movie_id, "like")
        fb = get_feedback(self.test_user_id, self.test_movie_id)
        self.assertEqual(fb, "like")

        remove_feedback(self.test_user_id, self.test_movie_id)
        self.assertIsNone(get_feedback(self.test_user_id, self.test_movie_id))

    # 10. Invalid Search Handling
    def test_10_invalid_search(self):
        # Extreme year range and gibberish string
        results, count = search_movies(query="xyz987noexisttitle123", year_min=1800, year_max=1850)
        self.assertEqual(count, 0)
        self.assertEqual(len(results), 0)

    # 11. AI Movie Assistant
    def test_11_ai_movie_assistant(self):
        assistant = get_assistant()
        q1 = assistant.answer_query("Recommend a movie for tonight", user_id=self.test_user_id)
        self.assertGreater(len(q1["movies"]), 0)

        q2 = assistant.answer_query("Suggest a mind-bending thriller", user_id=self.test_user_id)
        self.assertIn("Mind-bending", q2["context"])
        self.assertGreater(len(q2["movies"]), 0)

        q3 = assistant.answer_query("What should I watch after Star Wars?", user_id=self.test_user_id)
        self.assertGreater(len(q3["movies"]), 0)

    # 12. Latency Monitoring & Telemetry
    def test_12_latency_monitoring(self):
        registry = get_model_registry()
        registry.record_latency("Test Engine", latency_ms=12.5)
        registry.record_latency("Test Engine", latency_ms=15.0)

        stats = registry.get_latency_stats()
        self.assertGreater(stats["count"], 0)
        self.assertGreater(stats["avg_ms"], 0.0)
        self.assertGreater(stats["p50_ms"], 0.0)

    # 13. Continue Watching Deduplication & Distinct Records
    def test_13_continue_watching_deduplication(self):
        from services.history_service import get_continue_watching
        items = get_continue_watching(self.test_user_id, limit=6)
        movie_ids = [m["movie_id"] for m in items]
        self.assertEqual(len(movie_ids), len(set(movie_ids)), "Every movie in Continue Watching must be unique.")

    # 14. Rating Does Not Create Fake Watch History Entries
    def test_14_rating_does_not_affect_watch_history(self):
        conn = get_db_connection()
        try:
            # Pick a movie_id not currently in user 42's watch_history
            unwatched_row = conn.execute("""
                SELECT movie_id FROM movies 
                WHERE movie_id NOT IN (SELECT movie_id FROM watch_history WHERE user_id = ?) 
                LIMIT 1
            """, (self.test_user_id,)).fetchone()
            if unwatched_row:
                test_mid = unwatched_row["movie_id"]
                before_count = conn.execute("SELECT COUNT(*) FROM watch_history WHERE user_id = ? AND movie_id = ?", (self.test_user_id, test_mid)).fetchone()[0]
                self.assertEqual(before_count, 0)

                # Rate the movie
                rate_movie(self.test_user_id, test_mid, 5.0)

                # Verify rating exists
                self.assertEqual(get_user_rating(self.test_user_id, test_mid), 5.0)

                # Verify watch_history was NOT touched
                after_count = conn.execute("SELECT COUNT(*) FROM watch_history WHERE user_id = ? AND movie_id = ?", (self.test_user_id, test_mid)).fetchone()[0]
                self.assertEqual(after_count, 0, "Rating a movie must not insert into watch_history.")

                # Cleanup test rating
                from services.feedback_service import delete_rating
                delete_rating(self.test_user_id, test_mid)
        finally:
            conn.close()

    # 15. Poster Service and Graceful Fallback
    def test_15_poster_service_and_fallback(self):
        from services.poster_service import get_movie_poster_url
        # Real poster URL returned for known title
        toy_story_poster = get_movie_poster_url(1, "Toy Story (1995)")
        self.assertIsNotNone(toy_story_poster)
        self.assertTrue(toy_story_poster.startswith("http"))

        # Fallback (None) returned for unknown title
        unknown_poster = get_movie_poster_url(999999, "Unknown Random Movie Title 1928")
        self.assertIsNone(unknown_poster, "Unlisted titles should return None to trigger graceful fallback.")

    # 16. Supabase Service Safe Offline Handling
    def test_16_supabase_service_safe_offline_handling(self):
        from services.supabase_service import is_supabase_configured, get_credentials, sign_in_with_password
        creds = get_credentials()
        self.assertIn("url", creds)
        self.assertIn("publishable_key", creds)
        self.assertIn("secret_key", creds)

        # When credentials are not populated, sign_in should return graceful error instead of unhandled crash
        if not is_supabase_configured():
            res = sign_in_with_password("test@example.com", "password123")
            self.assertFalse(res["success"])
            self.assertIn("not configured", res["error"].lower())

    # 17. Netflix Hero Slider Movie Data Integrity
    def test_17_hero_slider_movie_data(self):
        from ui.hero_slider import FEATURED_HERO_MOVIES
        self.assertGreaterEqual(len(FEATURED_HERO_MOVIES), 5, "Hero slider must feature at least 5 movies.")
        for m in FEATURED_HERO_MOVIES:
            self.assertIn("id", m)
            self.assertIn("title", m)
            self.assertIn("backdrop", m)
            self.assertIn("overview", m)
            self.assertTrue(m["backdrop"].startswith("http"), f"Backdrop for {m['title']} must be a valid URL.")

    # 18. Video & Demo Trailer Service
    def test_18_video_service(self):
        from services.video_service import get_movie_video_info
        info = get_movie_video_info(10003, "Interstellar")
        self.assertIn("video_url", info)
        self.assertTrue(info["video_url"].startswith("http"))
        self.assertIn("duration", info)


if __name__ == "__main__":
    unittest.main()
