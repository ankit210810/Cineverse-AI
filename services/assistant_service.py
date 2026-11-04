"""AI Movie Assistant Service for Cineverse AI.

Processes natural language movie inquiries using the Cineverse recommendation engines,
content-similarity matching, mood mapping, and database metadata without fake LLM hallucinations.
"""

import re
from typing import Dict, List, Optional, Any
from database.db import get_db_connection
from services.movie_service import (
    search_movies,
    get_mood_movies,
    get_similar_movies,
    get_movie,
    MOOD_GENRE_MAP
)
from services.recommendation_service import get_recommendation_service
from services.user_service import get_user_taste_profile


class CineverseAssistant:

    def __init__(self):
        self.rec_service = get_recommendation_service()

    def answer_query(self, query: str, user_id: int) -> Dict[str, Any]:
        """Analyze user question and return curated movie recommendations with natural commentary."""
        clean_q = query.strip().lower()

        # Intent 1: "after <movie>" or "similar to <movie>"
        similar_match = re.search(r'(?:after|similar to|like)\s+([a-zA-Z0-9\s\:\'\-]+)', clean_q)
        if similar_match and "favourites" not in clean_q and "favorites" not in clean_q and "what i" not in clean_q:
            candidate_title = similar_match.group(1).strip()
            # Remove trailing filler words
            candidate_title = re.sub(r'\b(tonight|movie|movies|please|recommend)\b', '', candidate_title).strip()
            if len(candidate_title) >= 3:
                return self._handle_similar_title(candidate_title, user_id)

        # Intent 2: "similar to my favourites" or "recommend for me"
        if any(k in clean_q for k in ["my favourite", "my favorite", "my taste", "what i like", "based on my"]):
            return self._handle_user_taste(user_id)

        # Intent 3: Mood-based matching
        for mood, details in MOOD_GENRE_MAP.items():
            if mood.lower() in clean_q:
                return self._handle_mood_request(mood, user_id)

        if "mind-bending" in clean_q or "mind bending" in clean_q or "puzzle" in clean_q:
            return self._handle_mood_request("Mind-bending", user_id)
        if "funny" in clean_q or "relax" in clean_q or "laugh" in clean_q or "chill" in clean_q:
            return self._handle_mood_request("Relaxed", user_id)
        if "scary" in clean_q or "horror" in clean_q:
            return self._handle_genre_request("Horror", user_id)
        if "action" in clean_q or "thrill" in clean_q:
            return self._handle_mood_request("Suspenseful", user_id)
        if "romance" in clean_q or "romantic" in clean_q or "love" in clean_q:
            return self._handle_mood_request("Romantic", user_id)
        if "sad" in clean_q or "cry" in clean_q or "tearjerker" in clean_q:
            return self._handle_mood_request("Sad", user_id)
        if "adventure" in clean_q or "epic" in clean_q:
            return self._handle_mood_request("Adventurous", user_id)
        if "cold start" in clean_q or "space heist" in clean_q or "2026" in clean_q or "new movie" in clean_q:
            return self._handle_cold_start_inquiry(user_id)

        # Intent 4: Default tonight / general recommendation
        return self._handle_general_tonight(user_id)

    def _handle_similar_title(self, title_query: str, user_id: int) -> Dict[str, Any]:
        """Find movies similar to the requested title."""
        conn = get_db_connection()
        try:
            # Search for best matching title in database
            matched = conn.execute("""
                SELECT movie_id, title, release_year, genres
                FROM movies
                WHERE title LIKE ?
                ORDER BY LENGTH(title) ASC
                LIMIT 1
            """, (f"%{title_query}%",)).fetchone()

            if not matched:
                # If title like 'Interstellar' is queried and not in 1998 MovieLens, look for sci-fi/space epics
                if "interstellar" in title_query or "matrix" in title_query or "star wars" in title_query:
                    fallback_title = "Star Wars (1977)"
                    matched = conn.execute("SELECT movie_id, title, release_year, genres FROM movies WHERE title LIKE '%Star Wars%' LIMIT 1").fetchone()

            if not matched:
                return {
                    "intro": f"I couldn't locate '{title_query}' in our archive, but here are celebrated titles featuring related cinematic themes:",
                    "movies": get_mood_movies("Adventurous", limit=4),
                    "context": "Archive thematic fallback"
                }

            source_movie_id = matched["movie_id"]
            source_title = matched["title"]
            similar = get_similar_movies(source_movie_id, limit=4)

            return {
                "intro": f"Because you enjoyed **{source_title}**, here are top-tier films that share its thematic DNA, genre atmosphere, and narrative pacing:",
                "movies": similar,
                "context": f"Content-based similarity to '{source_title}'"
            }
        finally:
            conn.close()

    def _handle_user_taste(self, user_id: int) -> Dict[str, Any]:
        """Recommend based on user's actual taste profile and top genres."""
        profile = get_user_taste_profile(user_id)
        top_genres = profile.get("top_genres", ["Drama", "Action"])
        rec_res = self.rec_service.get_recommendations(user_id, algorithm="Automatic Best Model", limit=4)

        intro = (
            f"Analyzing your taste profile ({', '.join(top_genres[:3]) if top_genres else 'Eclectic'}), "
            f"our **{rec_res['algorithm']}** selected these tailored stories for you:"
        )

        return {
            "intro": intro,
            "movies": rec_res["recommendations"],
            "context": f"Personalized via {rec_res['algorithm']}"
        }

    def _handle_mood_request(self, mood: str, user_id: int) -> Dict[str, Any]:
        """Recommend based on requested mood."""
        mood_info = MOOD_GENRE_MAP.get(mood, {})
        tagline = mood_info.get("tagline", "Curated for your current mood.")
        movies = get_mood_movies(mood, limit=4)

        intro = f"In the mood for **{mood}**? {tagline} Here are our top-rated recommendations:"
        return {
            "intro": intro,
            "movies": movies,
            "context": f"Mood Discovery: {mood}"
        }

    def _handle_genre_request(self, genre: str, user_id: int) -> Dict[str, Any]:
        """Recommend top rated movies in a given genre."""
        movies, _ = search_movies(genres=[genre], sort_by="popularity", limit=4)
        intro = f"Here are the most acclaimed **{genre}** films in the Cineverse catalog:"
        return {
            "intro": intro,
            "movies": movies,
            "context": f"Genre Filter: {genre}"
        }

    def _handle_cold_start_inquiry(self, user_id: int) -> Dict[str, Any]:
        """Highlight cold-start recommendation mechanics featuring Space Heist 2026."""
        cold_res = self.rec_service.get_recommendations(
            user_id,
            algorithm="Cold-Start Metadata Matching",
            limit=4
        )
        intro = (
            "Here is Cineverse's **Cold-Start Metadata Engine** in action! "
            "Notice how **'Space Heist 2026'** (a brand new unrated test title) is recommended "
            "by blending its genre tags (Sci-Fi, Thriller, Adventure) and release year with your profile:"
        )
        return {
            "intro": intro,
            "movies": cold_res["recommendations"],
            "context": "Cold-Start Metadata Matching"
        }

    def _handle_general_tonight(self, user_id: int) -> Dict[str, Any]:
        """General recommendation for tonight using Automatic Best Model."""
        rec_res = self.rec_service.get_recommendations(user_id, algorithm="Automatic Best Model", limit=4)
        intro = (
            f"Here is your personalized cinematic lineup for tonight, generated using "
            f"**{rec_res['algorithm']}** (measured latency: {rec_res['latency_ms']} ms):"
        )
        return {
            "intro": intro,
            "movies": rec_res["recommendations"],
            "context": f"Engine: {rec_res['algorithm']}"
        }


_assistant: Optional[CineverseAssistant] = None


def get_assistant() -> CineverseAssistant:
    global _assistant
    if _assistant is None:
        _assistant = CineverseAssistant()
    return _assistant
