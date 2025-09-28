import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")
# If using SQLite, enable check_same_thread=False in engine creation (see database.py).
