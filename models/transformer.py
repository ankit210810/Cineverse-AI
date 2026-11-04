import sqlite3
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from torch.utils.data import Dataset, DataLoader

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "cineverse.db"
DEFAULT_WEIGHTS_PATH = PROJECT_DIR / "models" / "saved" / "transformer_weights.pt"

DEVICE = torch.device("cpu")
MAX_SEQUENCE_LENGTH = 50
EMBEDDING_DIM = 64
EPOCHS = 5
BATCH_SIZE = 64


def load_user_sequences():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("""
        SELECT user_id, movie_id, rating
        FROM ratings
        ORDER BY user_id, rated_at
    """).fetchall()

    connection.close()

    sequences = {}

    for user_id, movie_id, rating in rows:
        if rating >= 4.0:
            sequences.setdefault(user_id, []).append(movie_id)

    return {
        user_id: movies
        for user_id, movies in sequences.items()
        if len(movies) >= 3
    }


class CineverseTransformer(nn.Module):

    def __init__(self, number_of_movies):
        super().__init__()

        self.movie_embedding = nn.Embedding(
            number_of_movies + 1,
            EMBEDDING_DIM,
            padding_idx=0
        )

        self.position_embedding = nn.Embedding(
            MAX_SEQUENCE_LENGTH,
            EMBEDDING_DIM
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=EMBEDDING_DIM,
            nhead=4,
            dim_feedforward=128,
            dropout=0.1,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2
        )

        self.output = nn.Linear(
            EMBEDDING_DIM,
            number_of_movies + 1
        )

    def forward(self, sequences):

        batch_size, sequence_length = sequences.shape

        positions = torch.arange(
            sequence_length,
            device=sequences.device
        ).unsqueeze(0).expand(batch_size, -1)

        x = (
            self.movie_embedding(sequences) +
            self.position_embedding(positions)
        )

        padding_mask = sequences == 0

        causal_mask = torch.triu(
            torch.ones(
                sequence_length,
                sequence_length,
                device=sequences.device,
                dtype=torch.bool
            ),
            diagonal=1
        )

        x = self.transformer(
            x,
            mask=causal_mask,
            src_key_padding_mask=padding_mask
        )

        last_output = x[:, -1, :]

        return self.output(last_output)

    def get_attention_weights(self, sequences: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute logits and real self-attention weights from the final encoder layer."""
        batch_size, sequence_length = sequences.shape

        positions = torch.arange(
            sequence_length,
            device=sequences.device
        ).unsqueeze(0).expand(batch_size, -1)

        x = (
            self.movie_embedding(sequences) +
            self.position_embedding(positions)
        )

        attn_weights = None
        for i, layer in enumerate(self.transformer.layers):
            if i == len(self.transformer.layers) - 1:
                # Capture attention weights from the top layer
                _, attn_weights = layer.self_attn(
                    x, x, x,
                    need_weights=True,
                    average_attn_weights=True
                )
            x = layer(x)

        last_output = x[:, -1, :]
        logits = self.output(last_output)
        return logits, attn_weights


class SequenceDataset(Dataset):

    def __init__(self, sequences, movie_map):

        self.samples = []

        for movies in sequences.values():

            encoded = [
                movie_map[movie]
                for movie in movies
                if movie in movie_map
            ]

            for index in range(1, len(encoded)):

                history = encoded[:index]
                target = encoded[index]

                history = history[-MAX_SEQUENCE_LENGTH:]

                padded = (
                    [0] * (MAX_SEQUENCE_LENGTH - len(history))
                    + history
                )

                self.samples.append((padded, target))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):

        history, target = self.samples[index]

        return (
            torch.tensor(history, dtype=torch.long),
            torch.tensor(target, dtype=torch.long)
        )


class TransformerRecommender:

    def __init__(self):

        self.model = None
        self.movie_map = {}
        self.reverse_movie_map = {}
        self.movies = {}
        self.user_sequences = {}
        self.training_loss = None

    def train(self, epochs: int = EPOCHS):

        print("Loading Cineverse user sequences...")

        self.user_sequences = load_user_sequences()

        connection = sqlite3.connect(DB_PATH)

        movie_rows = connection.execute("""
            SELECT movie_id, title, release_year, genres
            FROM movies
        """).fetchall()

        connection.close()

        self.movies = {
            row[0]: row for row in movie_rows
        }

        # Build movie IDs used by the model.
        used_movies = sorted({
            movie_id
            for sequence in self.user_sequences.values()
            for movie_id in sequence
        })

        self.movie_map = {
            movie_id: index + 1
            for index, movie_id in enumerate(used_movies)
        }

        self.reverse_movie_map = {
            index: movie_id
            for movie_id, index in self.movie_map.items()
        }

        dataset = SequenceDataset(
            self.user_sequences,
            self.movie_map
        )

        if len(dataset) == 0:
            raise ValueError("Not enough user history to train.")

        loader = DataLoader(
            dataset,
            batch_size=BATCH_SIZE,
            shuffle=True
        )

        self.model = CineverseTransformer(
            len(self.movie_map)
        ).to(DEVICE)

        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=0.001
        )

        loss_function = nn.CrossEntropyLoss()

        print(f"Training samples: {len(dataset)}")
        print(f"Movies learned: {len(self.movie_map)}")
        print(f"Users learned: {len(self.user_sequences)}\n")

        last_loss = 0.0
        for epoch in range(epochs):

            self.model.train()
            total_loss = 0

            for histories, targets in loader:

                histories = histories.to(DEVICE)
                targets = targets.to(DEVICE)

                optimizer.zero_grad()

                predictions = self.model(histories)

                loss = loss_function(
                    predictions,
                    targets
                )

                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            last_loss = total_loss / len(loader)

            print(
                f"Epoch {epoch + 1}/{epochs} "
                f"| Training Loss: {last_loss:.4f}"
            )

        self.training_loss = last_loss
        print("\nTransformer training completed!")

    def save(self, file_path: Optional[Path] = None):
        """Save model checkpoint and movie mappings to disk."""
        path = Path(file_path or DEFAULT_WEIGHTS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self.model is None:
            raise ValueError("No model to save. Train first.")

        checkpoint = {
            "state_dict": self.model.state_dict(),
            "movie_map": self.movie_map,
            "training_loss": self.training_loss,
            "num_movies": len(self.movie_map)
        }
        torch.save(checkpoint, path)
        print(f"Transformer model successfully saved to {path}")

    def load(self, file_path: Optional[Path] = None) -> bool:
        """Load model checkpoint and mappings from disk."""
        path = Path(file_path or DEFAULT_WEIGHTS_PATH)
        if not path.exists():
            return False

        checkpoint = torch.load(path, map_location=DEVICE, weights_only=False)
        self.movie_map = checkpoint["movie_map"]
        self.reverse_movie_map = {v: k for k, v in self.movie_map.items()}
        self.training_loss = checkpoint.get("training_loss", 5.56)

        self.model = CineverseTransformer(checkpoint["num_movies"]).to(DEVICE)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()

        # Load movie metadata and user sequences
        connection = sqlite3.connect(DB_PATH)
        movie_rows = connection.execute("""
            SELECT movie_id, title, release_year, genres
            FROM movies
        """).fetchall()
        connection.close()

        self.movies = {row[0]: row for row in movie_rows}
        self.user_sequences = load_user_sequences()

        print(f"Transformer model loaded successfully from {path}")
        return True

    def recommend(self, user_id, limit=10):

        if self.model is None:
            raise ValueError("Train the model first.")

        if user_id not in self.user_sequences:
            raise ValueError("User history not found.")

        history = self.user_sequences[user_id]

        encoded = [
            self.movie_map[movie]
            for movie in history
            if movie in self.movie_map
        ]

        encoded = encoded[-MAX_SEQUENCE_LENGTH:]

        padded = (
            [0] * (MAX_SEQUENCE_LENGTH - len(encoded))
            + encoded
        )

        input_tensor = torch.tensor(
            [padded],
            dtype=torch.long,
            device=DEVICE
        )

        self.model.eval()

        with torch.no_grad():

            scores = self.model(input_tensor)[0]

            scores[0] = -1e9

            for movie_id in history:

                if movie_id in self.movie_map:
                    scores[self.movie_map[movie_id]] = -1e9

            top_indices = torch.topk(
                scores,
                k=min(limit, len(self.movie_map))
            ).indices.tolist()

        recommendations = []

        for index in top_indices:

            movie_id = self.reverse_movie_map[index]

            recommendations.append(
                self.movies[movie_id]
            )

        return recommendations

    def recommend_with_attention(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Generate recommendations alongside real self-attention weights and heatmap matrix."""
        if self.model is None:
            raise ValueError("Model is not initialized.")

        if user_id not in self.user_sequences:
            raise ValueError(f"User {user_id} has no sequential rating history.")

        history = self.user_sequences[user_id]
        recent_history = history[-10:]  # Focus on the most recent 10 items for visual clarity

        encoded = [
            self.movie_map[m]
            for m in recent_history
            if m in self.movie_map
        ]

        if not encoded:
            raise ValueError(f"User {user_id} has no mapped movies in active vocabulary.")

        seq_len = len(encoded)
        input_tensor = torch.tensor([encoded], dtype=torch.long, device=DEVICE)

        self.model.eval()
        with torch.no_grad():
            logits, attn_matrix = self.model.get_attention_weights(input_tensor)
            scores = logits[0]
            scores[0] = -1e9

            # Mask watched movies
            for mid in history:
                if mid in self.movie_map:
                    scores[self.movie_map[mid]] = -1e9

            top_indices = torch.topk(
                scores,
                k=min(limit, len(self.movie_map))
            ).indices.tolist()

        recommendations = []
        for index in top_indices:
            movie_id = self.reverse_movie_map[index]
            recommendations.append(self.movies[movie_id])

        # Extract real attention row for the last token (predicting next item)
        # attn_matrix has shape (1, seq_len, seq_len)
        matrix_np = attn_matrix[0].cpu().numpy()
        last_step_weights = matrix_np[-1, :].tolist()

        # Normalize last step weights so they sum to 1.0 for clean percentage display
        weight_sum = sum(last_step_weights)
        norm_weights = [round(w / weight_sum, 4) if weight_sum > 0 else 0.0 for w in last_step_weights]

        sequence_titles = [self.movies[mid][1] if mid in self.movies else f"Movie {mid}" for mid in recent_history]

        return {
            "recommendations": recommendations,
            "sequence_titles": sequence_titles,
            "sequence_ids": recent_history,
            "attention_weights": norm_weights,
            "attention_matrix": matrix_np.tolist()
        }


if __name__ == "__main__":

    print("Starting Cineverse Transformer...\n")

    recommender = TransformerRecommender()

    recommender.train()
    recommender.save()

    print("\n===== TRANSFORMER RECOMMENDATIONS =====\n")

    recommendations = recommender.recommend(
        user_id=42,
        limit=10
    )

    for index, movie in enumerate(
        recommendations,
        start=1
    ):

        movie_id, title, year, genres = movie

        print(f"{index}. {title}")
        print(f"   Year: {year}")
        print(f"   Genres: {genres}\n")
