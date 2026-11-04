import sqlite3
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "cineverse.db"
DEFAULT_WEIGHTS_PATH = PROJECT_DIR / "models" / "saved" / "mf_weights.npz"


class MatrixFactorization:

    def __init__(self, factors=32, learning_rate=0.01,
                 regularization=0.02, epochs=15):

        self.factors = factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.epochs = epochs

        self.user_map = {}
        self.movie_map = {}
        self.reverse_movie_map = {}
        self.user_factors = None
        self.movie_factors = None
        self.global_mean = 0.0
        self.movies = []
        self.training_rmse = None

    def load_data(self):

        connection = sqlite3.connect(DB_PATH)

        ratings = connection.execute("""
            SELECT user_id, movie_id, rating
            FROM ratings
        """).fetchall()

        movies = connection.execute("""
            SELECT movie_id, title, release_year, genres
            FROM movies
        """).fetchall()

        connection.close()

        return ratings, movies

    def train(self):

        ratings, self.movies = self.load_data()

        users = sorted(set(row[0] for row in ratings))
        movie_ids = sorted(set(row[1] for row in ratings))

        self.user_map = {
            user: index for index, user in enumerate(users)
        }

        self.movie_map = {
            movie: index for index, movie in enumerate(movie_ids)
        }

        self.reverse_movie_map = {
            index: movie for movie, index in self.movie_map.items()
        }

        rng = np.random.default_rng(42)

        self.user_factors = rng.normal(
            0, 0.1, (len(users), self.factors)
        )

        self.movie_factors = rng.normal(
            0, 0.1, (len(movie_ids), self.factors)
        )

        self.global_mean = float(np.mean([
            row[2] for row in ratings
        ]))

        rmse = 0.0
        for epoch in range(self.epochs):

            rng.shuffle(ratings)

            total_error = 0.0

            for user_id, movie_id, actual_rating in ratings:

                u = self.user_map[user_id]
                m = self.movie_map[movie_id]

                prediction = (
                    self.global_mean +
                    np.dot(
                        self.user_factors[u],
                        self.movie_factors[m]
                    )
                )

                error = actual_rating - prediction
                total_error += error ** 2

                user_old = self.user_factors[u].copy()
                movie_old = self.movie_factors[m].copy()

                self.user_factors[u] += self.learning_rate * (
                    error * movie_old -
                    self.regularization * user_old
                )

                self.movie_factors[m] += self.learning_rate * (
                    error * user_old -
                    self.regularization * movie_old
                )

            rmse = float(np.sqrt(total_error / len(ratings)))

            print(
                f"Epoch {epoch + 1}/{self.epochs} "
                f"| Training RMSE: {rmse:.4f}"
            )

        self.training_rmse = rmse
        print("\nMatrix Factorization training completed!")

    def save(self, file_path: Optional[Path] = None):
        """Save trained weights, embeddings, and mappings to disk."""
        path = Path(file_path or DEFAULT_WEIGHTS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        user_keys = np.array(list(self.user_map.keys()))
        user_vals = np.array(list(self.user_map.values()))
        movie_keys = np.array(list(self.movie_map.keys()))
        movie_vals = np.array(list(self.movie_map.values()))

        np.savez_compressed(
            path,
            user_factors=self.user_factors,
            movie_factors=self.movie_factors,
            global_mean=np.array([self.global_mean]),
            training_rmse=np.array([self.training_rmse or 0.0]),
            user_keys=user_keys,
            user_vals=user_vals,
            movie_keys=movie_keys,
            movie_vals=movie_vals
        )
        print(f"Matrix Factorization model saved to {path}")

    def load(self, file_path: Optional[Path] = None) -> bool:
        """Load trained weights, embeddings, and mappings from disk."""
        path = Path(file_path or DEFAULT_WEIGHTS_PATH)
        if not path.exists():
            return False

        data = np.load(path, allow_pickle=True)
        self.user_factors = data["user_factors"]
        self.movie_factors = data["movie_factors"]
        self.global_mean = float(data["global_mean"][0])
        self.training_rmse = float(data["training_rmse"][0])

        user_keys = data["user_keys"]
        user_vals = data["user_vals"]
        self.user_map = {int(k): int(v) for k, v in zip(user_keys, user_vals)}

        movie_keys = data["movie_keys"]
        movie_vals = data["movie_vals"]
        self.movie_map = {int(k): int(v) for k, v in zip(movie_keys, movie_vals)}
        self.reverse_movie_map = {v: k for k, v in self.movie_map.items()}

        # Load movie metadata
        connection = sqlite3.connect(DB_PATH)
        self.movies = connection.execute("""
            SELECT movie_id, title, release_year, genres
            FROM movies
        """).fetchall()
        connection.close()

        print(f"Matrix Factorization model loaded successfully from {path}")
        return True

    def recommend(self, user_id, limit=10):

        if self.user_factors is None or len(self.user_map) == 0:
            raise ValueError("Model is not trained. Call train() or load() first.")

        if user_id not in self.user_map:
            raise ValueError("User not found in training data.")

        if not self.movies:
            connection = sqlite3.connect(DB_PATH)
            self.movies = connection.execute("""
                SELECT movie_id, title, release_year, genres
                FROM movies
            """).fetchall()
            connection.close()

        user_index = self.user_map[user_id]

        scores = (
            self.global_mean +
            self.movie_factors @ self.user_factors[user_index]
        )

        rated = {
            self.movie_map[movie_id]
            for movie_id, in self._get_rated_movies(user_id)
            if movie_id in self.movie_map
        }

        ranked = np.argsort(scores)[::-1]

        movie_lookup = {
            row[0]: row for row in self.movies
        }

        recommendations = []

        for index in ranked:

            if index in rated:
                continue

            movie_id = self.reverse_movie_map[index]
            if movie_id in movie_lookup:
                recommendations.append(
                    (movie_lookup[movie_id], round(float(scores[index]), 3))
                )

            if len(recommendations) == limit:
                break

        return recommendations

    def _get_rated_movies(self, user_id):

        connection = sqlite3.connect(DB_PATH)

        result = connection.execute("""
            SELECT movie_id
            FROM ratings
            WHERE user_id = ?
        """, (user_id,)).fetchall()

        connection.close()

        return result


if __name__ == "__main__":

    model = MatrixFactorization()

    print("Training Cineverse Matrix Factorization...\n")

    model.train()
    model.save()

    print("\n===== RECOMMENDATIONS FOR MOVIELENS USER 42 =====\n")

    recommendations = model.recommend(user_id=42)

    for index, (movie, score) in enumerate(
        recommendations, start=1
    ):

        movie_id, title, year, genres = movie

        print(f"{index}. {title}")
        print(f"   Year: {year}")
        print(f"   Genres: {genres}")
        print(f"   Predicted rating: {score}/5")
        print()
