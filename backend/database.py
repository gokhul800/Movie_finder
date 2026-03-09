import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "movies.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "mymoviedb.csv")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT,
            overview       TEXT,
            genre          TEXT,
            language       TEXT,
            year           INTEGER,
            rating         REAL,
            popularity     REAL,
            vote_count     INTEGER,
            poster_url     TEXT
        )
    """)

    # Load CSV only if the table is empty
    cursor.execute("SELECT COUNT(*) FROM movies")
    if cursor.fetchone()[0] == 0:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                # Extract year from Release_Date (format: YYYY-MM-DD)
                release_date = row.get("Release_Date") or ""
                try:
                    year = int(release_date.split("-")[0]) if release_date else 0
                except (ValueError, IndexError):
                    year = 0

                # Skip rows with no title or invalid year
                title = (row.get("Title") or "").strip()
                if not title or year == 0:
                    continue

                rows.append((
                    title,
                    (row.get("Overview") or ""),
                    (row.get("Genre") or ""),
                    (row.get("Original_Language") or ""),
                    year,
                    float(row.get("Vote_Average") or 0),
                    float(row.get("Popularity") or 0),
                    int(float(row.get("Vote_Count") or 0)),
                    (row.get("Poster_Url") or ""),
                ))
            cursor.executemany(
                "INSERT INTO movies (title, overview, genre, language, year, rating, popularity, vote_count, poster_url) "
                "VALUES (?,?,?,?,?,?,?,?,?)", rows
            )
        print(f"Loaded {len(rows)} movies into the database.")
    else:
        print("Database already populated, skipping CSV import.")

    conn.commit()
    conn.close()


def query_movies(
    genre=None,
    language=None,
    year_start=None,
    year_end=None,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM movies WHERE 1=1"
    params = []

    if genre:
        # Genre field can be comma-separated, use LIKE for partial match
        sql += " AND genre LIKE ?"
        params.append(f"%{genre}%")
    if language:
        sql += " AND language = ?"
        params.append(language)
    if year_start:
        sql += " AND year >= ?"
        params.append(int(year_start))
    if year_end:
        sql += " AND year <= ?"
        params.append(int(year_end))

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
