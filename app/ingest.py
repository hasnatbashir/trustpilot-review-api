import argparse
import hashlib
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from .database import SessionLocal, engine
from .models import Base, User, Business, Review
from .metadata import IngestMetadata
from app.constants import (
    RENAME_MAP,
    F_REVIEW_ID,
    F_USER_ID,
    F_USER_NAME,
    F_EMAIL,
    F_COUNTRY,
    F_BUSINESS_ID,
    F_BUSINESS_NAME,
    F_RATING,
    F_TITLE,
    F_TEXT,
    F_IP,
    F_CREATED_AT,
    F_SOURCE_PATH,
    F_TOTAL_ROWS,
    F_LOADED_ROWS,
    F_FILE_HASH,
)


def compute_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataframe(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns=RENAME_MAP)
    if F_CREATED_AT in df.columns:
        df[F_CREATED_AT] = pd.to_datetime(df[F_CREATED_AT], errors="coerce", utc=True)
    return df


def upsert_dimension(session: Session, model, key_field: str, df: pd.DataFrame, fields: list[str]):
    """Batch upsert for dimension tables (users, businesses)."""
    existing_keys = set(
        k for (k,) in session.execute(text(f"SELECT {key_field} FROM {model.__tablename__}")).all()
    )
    to_insert = df[[key_field] + fields].drop_duplicates()
    to_insert = to_insert[~to_insert[key_field].isin(existing_keys)]
    objects = [
        model(**{k: (None if pd.isna(v) else v) for k, v in rec.items()})
        for rec in to_insert.to_dict("records")
    ]
    if objects:
        session.add_all(objects)


def ingest_csv(db: Session, csv_path: str):
    file_hash = compute_file_hash(csv_path)
    df = load_dataframe(csv_path)
    total_rows = len(df)

    # --- Upsert users & businesses ---
    user_cols = [c for c in [F_USER_ID, F_USER_NAME, F_EMAIL, F_COUNTRY] if c in df.columns]
    biz_cols = [c for c in [F_BUSINESS_ID, F_BUSINESS_NAME] if c in df.columns]

    if F_USER_ID in df.columns:
        upsert_dimension(db, User, F_USER_ID, df[user_cols], [c for c in user_cols if c != F_USER_ID])
    if F_BUSINESS_ID in df.columns:
        upsert_dimension(db, Business, F_BUSINESS_ID, df[biz_cols], [c for c in biz_cols if c != F_BUSINESS_ID])

    # --- Insert reviews (append-only) ---
    existing_review_ids = set(k for (k,) in db.execute(text("SELECT review_id FROM reviews")).all())
    review_cols = [c for c in [F_REVIEW_ID, F_USER_ID, F_BUSINESS_ID, F_RATING, F_TITLE, F_TEXT, F_IP, F_CREATED_AT] if c in df.columns]
    review_df = df[review_cols].drop_duplicates(subset=[F_REVIEW_ID])
    review_df = review_df[~review_df[F_REVIEW_ID].isin(existing_review_ids)]

    review_objs = []
    for rec in review_df.to_dict("records"):
        if F_CREATED_AT in rec and pd.notna(rec[F_CREATED_AT]):
            if isinstance(rec[F_CREATED_AT], pd.Timestamp):
                rec[F_CREATED_AT] = rec[F_CREATED_AT].to_pydatetime()
        review_objs.append(Review(**{k: (None if pd.isna(v) else v) for k, v in rec.items()}))

    if review_objs:
        db.add_all(review_objs)

    db.add(IngestMetadata(
        **{
            F_SOURCE_PATH: csv_path,
            F_TOTAL_ROWS: total_rows,
            F_LOADED_ROWS: len(review_objs),
            F_FILE_HASH: file_hash,
        }
    ))
    db.commit()
    print(f"Ingest complete. Rows in: {total_rows}, reviews loaded: {len(review_objs)}")


def run(csv_path: str):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        ingest_csv(session, csv_path=csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest reviews CSV file")
    parser.add_argument("--csv", required=True, help="Path to reviews CSV file")
    args = parser.parse_args()
    run(args.csv)
