from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import random
import os

from database import initialize_db, query_movies, get_all_movies
from model import get_recommendations

app = FastAPI(title="MovieFinder API", version="2.0.0")

# Allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
def startup_event():
    initialize_db()
    print("Database initialized successfully.")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/recommend")
def recommend(
    genre: str = Query(None),
    language: str = Query(None),
    year_start: int = Query(None),
    year_end: int = Query(None),
):
    # Step 1: Filter movies from database
    filtered = query_movies(
        genre=genre,
        language=language,
        year_start=year_start,
        year_end=year_end,
    )

    if not filtered:
        return {"results": [], "total_filtered": 0}

    # Step 2: Get all movies for stable encoding
    all_movies = get_all_movies()

    # Step 3: KNN + ranking
    recommendations = get_recommendations(filtered, all_movies, top_n=10)

    return {
        "results": recommendations,
        "total_filtered": len(filtered),
    }


@app.get("/surprise")
def surprise():
    """Return a randomly selected high-rated movie (rating >= 8.0)."""
    all_movies = get_all_movies()
    high_rated = [m for m in all_movies if m["rating"] >= 8.0]
    if not high_rated:
        high_rated = all_movies

    movie = random.choice(high_rated)
    return {
        "results": [{
            "movie_id": movie["movie_id"],
            "title": movie["title"],
            "overview": movie.get("overview", ""),
            "genre": movie["genre"],
            "year": movie["year"],
            "rating": movie["rating"],
            "language": movie.get("language", ""),
            "poster_url": movie["poster_url"],
        }],
        "total_filtered": 1,
    }


@app.get("/filters")
def get_filters():
    """Return unique filter values from the database for populating dropdowns."""
    all_movies = get_all_movies()

    # Collect individual genres (split comma-separated values)
    genre_set = set()
    for m in all_movies:
        for g in m["genre"].split(","):
            g = g.strip()
            if g:
                genre_set.add(g)

    genres = sorted(genre_set)
    languages = sorted(set(m["language"] for m in all_movies if m["language"]))
    years = sorted(set(m["year"] for m in all_movies if m["year"]))

    return {
        "genres": genres,
        "languages": languages,
        "year_min": min(years) if years else 2000,
        "year_max": max(years) if years else 2024,
    }
