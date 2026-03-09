import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "knn_model.pkl")

FEATURE_COLS = ["genre", "language"]


def build_feature_matrix(movies: list[dict]):
    """Build feature matrix using One-Hot Encoding of categorical columns."""
    data = [[m[col] for col in FEATURE_COLS] for m in movies]
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X = encoder.fit_transform(data)
    return X, encoder


def train_knn(X: np.ndarray, n_neighbors: int = 10):
    """Train KNN model with cosine similarity."""
    k = min(n_neighbors, len(X))
    knn = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute")
    knn.fit(X)
    return knn


def get_recommendations(filtered_movies: list[dict], all_movies: list[dict], top_n: int = 10):
    """
    Use KNN cosine similarity on filtered movies.
    Rank by: similarity score → rating → popularity.
    Returns top_n movie dicts (with fields trimmed for API response).
    """
    if not filtered_movies:
        return []

    if len(filtered_movies) <= top_n:
        # Not enough to run KNN meaningfully – rank directly
        ranked = sorted(
            filtered_movies,
            key=lambda m: (m["rating"], m["popularity"]),
            reverse=True,
        )
        return _format_results(ranked[:top_n])

    # Build encoder on all movies for a stable feature space
    all_data = [[m[col] for col in FEATURE_COLS] for m in all_movies]
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoder.fit(all_data)

    # Encode filtered movies
    filtered_data = [[m[col] for col in FEATURE_COLS] for m in filtered_movies]
    X_filtered = encoder.transform(filtered_data)

    # Train KNN on filtered subset
    k = min(top_n + 1, len(filtered_movies))
    knn = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute")
    knn.fit(X_filtered)

    # Use centroid of filtered movies as query vector
    centroid = X_filtered.mean(axis=0, keepdims=True)
    distances, indices = knn.kneighbors(centroid)

    # Build scored result list
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        similarity = 1.0 - dist
        movie = dict(filtered_movies[idx])
        movie["_similarity"] = similarity
        results.append(movie)

    # Rank by similarity (desc), rating (desc), popularity (desc)
    results.sort(key=lambda m: (m["_similarity"], m["rating"], m["popularity"]), reverse=True)

    return _format_results(results[:top_n])


def _format_results(movies: list[dict]) -> list[dict]:
    """Return only the fields needed by the frontend."""
    output = []
    for m in movies:
        output.append({
            "movie_id": m["movie_id"],
            "title": m["title"],
            "overview": m.get("overview", ""),
            "genre": m["genre"],
            "year": m["year"],
            "rating": m["rating"],
            "language": m.get("language", ""),
            "poster_url": m["poster_url"],
        })
    return output
