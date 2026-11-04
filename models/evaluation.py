import sys
import sqlite3
import numpy as np
import torch
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "models") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "models"))

try:
    from models.popularity import get_popular_movies
    from models.matrix_factorization import MatrixFactorization
    from models.transformer import TransformerRecommender, SequenceDataset, CineverseTransformer
except ImportError:
    from popularity import get_popular_movies
    from matrix_factorization import MatrixFactorization
    from transformer import TransformerRecommender, SequenceDataset, CineverseTransformer

DB_PATH = PROJECT_DIR / "database" / "cineverse.db"

K = 10


def load_evaluation_data():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("""
        SELECT user_id, movie_id, rating, rated_at
        FROM ratings
        WHERE rating >= 4.0
        ORDER BY user_id, rated_at, rating_id
    """).fetchall()

    connection.close()

    histories = {}

    for user_id, movie_id, rating, rated_at in rows:
        histories.setdefault(user_id, []).append(movie_id)

    train_histories = {}
    test_items = {}

    for user_id, movies in histories.items():
        if len(movies) < 3:
            continue

        train_histories[user_id] = movies[:-1]
        test_items[user_id] = movies[-1]

    return train_histories, test_items


def recall_at_k(recommendations, actual_item, k=K):
    top_items = recommendations[:k]

    return 1.0 if actual_item in top_items else 0.0


def ndcg_at_k(recommendations, actual_item, k=K):
    top_items = recommendations[:k]

    if actual_item in top_items:
        rank = top_items.index(actual_item)
        return 1.0 / np.log2(rank + 2)

    return 0.0


def evaluate_rankings(rankings, test_items):
    recalls = []
    ndcgs = []

    for user_id, actual_item in test_items.items():

        recommendations = rankings.get(user_id, [])

        recalls.append(
            recall_at_k(recommendations, actual_item)
        )

        ndcgs.append(
            ndcg_at_k(recommendations, actual_item)
        )

    return (
        float(np.mean(recalls)),
        float(np.mean(ndcgs))
    )


def evaluate_popularity(test_items):
    popular = get_popular_movies(limit=1682)

    ranking = [
        movie[0]
        for movie in popular
    ]

    rankings = {
        user_id: ranking
        for user_id in test_items
    }

    return evaluate_rankings(rankings, test_items)


def evaluate_matrix_factorization(train_histories, test_items):
    model = MatrixFactorization(epochs=15)

    # Train the model using only training interactions.
    connection = sqlite3.connect(DB_PATH)

    all_ratings = connection.execute("""
        SELECT user_id, movie_id, rating
        FROM ratings
    """).fetchall()

    connection.close()

    allowed = {
        (user_id, movie_id)
        for user_id, movies in train_histories.items()
        for movie_id in movies
    }

    training_ratings = [
        row for row in all_ratings
        if (row[0], row[1]) in allowed
    ]

    users = sorted(set(row[0] for row in training_ratings))
    movie_ids = sorted(set(row[1] for row in training_ratings))

    user_map = {user: i for i, user in enumerate(users)}
    movie_map = {movie: i for i, movie in enumerate(movie_ids)}
    reverse_movie_map = {i: movie for movie, i in movie_map.items()}

    rng = np.random.default_rng(42)

    user_factors = rng.normal(0, 0.1, (len(users), 32))
    movie_factors = rng.normal(0, 0.1, (len(movie_ids), 32))

    global_mean = np.mean([row[2] for row in training_ratings])

    for epoch in range(15):
        rng.shuffle(training_ratings)

        for user_id, movie_id, actual in training_ratings:
            u = user_map[user_id]
            m = movie_map[movie_id]

            prediction = global_mean + np.dot(
                user_factors[u],
                movie_factors[m]
            )

            error = actual - prediction

            old_user = user_factors[u].copy()
            old_movie = movie_factors[m].copy()

            user_factors[u] += 0.01 * (
                error * old_movie - 0.02 * old_user
            )

            movie_factors[m] += 0.01 * (
                error * old_user - 0.02 * old_movie
            )

    rankings = {}

    for user_id in test_items:

        if user_id not in user_map:
            continue

        scores = (
            global_mean +
            movie_factors @ user_factors[user_map[user_id]]
        )

        rated = {
            movie_map[movie_id]
            for movie_id in train_histories[user_id]
            if movie_id in movie_map
        }

        ranked_indices = np.argsort(scores)[::-1]

        rankings[user_id] = [
            reverse_movie_map[index]
            for index in ranked_indices
            if index not in rated
        ][:K]

    return evaluate_rankings(rankings, test_items)


def evaluate_transformer(train_histories, test_items):
    connection = sqlite3.connect(DB_PATH)

    movie_rows = connection.execute("""
        SELECT movie_id
        FROM movies
    """).fetchall()

    connection.close()

    used_movies = sorted({
        movie_id
        for movies in train_histories.values()
        for movie_id in movies
    })

    movie_map = {
        movie_id: index + 1
        for index, movie_id in enumerate(used_movies)
    }

    reverse_movie_map = {
        index: movie_id
        for movie_id, index in movie_map.items()
    }

    dataset = SequenceDataset(
        train_histories,
        movie_map
    )

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=64,
        shuffle=True
    )

    model = CineverseTransformer(len(movie_map))

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001
    )

    loss_function = torch.nn.CrossEntropyLoss()

    print("Training Transformer for evaluation...")

    for epoch in range(5):
        model.train()
        total_loss = 0

        for histories, targets in loader:
            optimizer.zero_grad()

            predictions = model(histories)
            loss = loss_function(predictions, targets)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(
            f"Transformer evaluation epoch {epoch + 1}/5 "
            f"| Loss: {total_loss / len(loader):.4f}"
        )

    rankings = {}

    model.eval()

    for user_id, history in train_histories.items():

        if user_id not in test_items:
            continue

        encoded = [
            movie_map[movie]
            for movie in history
            if movie in movie_map
        ][-50:]

        padded = [0] * (50 - len(encoded)) + encoded

        with torch.no_grad():
            scores = model(
                torch.tensor([padded], dtype=torch.long)
            )[0]

        scores[0] = -1e9

        for movie_id in history:
            if movie_id in movie_map:
                scores[movie_map[movie_id]] = -1e9

        top_indices = torch.topk(
            scores,
            k=min(K, len(movie_map))
        ).indices.tolist()

        rankings[user_id] = [
            reverse_movie_map[index]
            for index in top_indices
        ]

    return evaluate_rankings(rankings, test_items)


if __name__ == "__main__":

    print("\n===== CINEVERSE MODEL EVALUATION =====\n")

    train_histories, test_items = load_evaluation_data()

    print(f"Evaluation users: {len(test_items)}")
    print("Metric: Recall@10 and NDCG@10")
    print("Split: Last positive interaction per user\n")

    print("Evaluating Popularity...")
    popularity_result = evaluate_popularity(test_items)

    print("\nEvaluating Matrix Factorization...")
    mf_result = evaluate_matrix_factorization(
        train_histories,
        test_items
    )

    print("\nEvaluating Transformer...")
    transformer_result = evaluate_transformer(
        train_histories,
        test_items
    )

    print("\n===== FINAL COMPARISON =====\n")

    print(f"{'Model':<25} {'Recall@10':<15} {'NDCG@10':<15}")

    print("-" * 55)

    results = [
        ("Popularity", popularity_result),
        ("Matrix Factorization", mf_result),
        ("Transformer", transformer_result)
    ]

    for name, (recall, ndcg) in results:
        print(f"{name:<25} {recall:<15.4f} {ndcg:<15.4f}")

    print("\nEvaluation completed!")
