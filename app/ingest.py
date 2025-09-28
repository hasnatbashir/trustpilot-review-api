import argparse
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import engine, SessionLocal
from .models import User, Business, Review, Base
from .metadata import IngestMetadata
from .validate import basic_validations
from datetime import datetime

def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # common aliases
    aliases = {
        "Reviewer Name": "user_name",
        "Review Title": "title",
        "Review Content": "text",
        "Review Rating": "rating",
        "Review IP Address": "ip_address",
        "Business Id": "business_id",
        "Business Name": "business_name",
        "Reviewer Id": "user_id",
        "Email Address": "email",
        "Reviewer Country": "country",
        "Review Date": "created_at",
        "Review Id": "review_id",
    }
    for old, new in list(aliases.items()):
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    # Parse dates if present
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    # Coerce rating to int where possible
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    return df

def upsert_dimension(session: Session, model, key_field: str, rows: pd.DataFrame, fields: list[str]):
    existing_keys = set(
        k for (k,) in session.execute(text(f"SELECT {key_field} FROM {model.__tablename__}")).all()
    )
    to_insert = rows[[key_field] + fields].drop_duplicates()
    to_insert = to_insert[~to_insert[key_field].isin(existing_keys)]
    objects = [model(**{k: (None if pd.isna(v) else v) for k, v in rec.items()}) for rec in to_insert.to_dict("records")]
    if objects:
        session.add_all(objects)

def run(csv_path: str):
    # Create tables
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        df = normalise_columns(df)
        basic_validations(df)

        # Derive dims from reviews
        user_cols = [c for c in ["user_id", "user_name", "email", "country"] if c in df.columns]
        biz_cols = [c for c in ["business_id", "business_name"] if c in df.columns]
        review_cols = ["review_id","user_id","business_id","rating","title","text", "ip_address","created_at"]
        review_cols = [c for c in review_cols if c in df.columns]

        # Upsert users, businesses
        if "user_id" in df.columns:
            upsert_dimension(session, User, "user_id", df[user_cols], [c for c in user_cols if c != "user_id"])
        if "business_id" in df.columns:
            upsert_dimension(session, Business, "business_id", df[biz_cols], [c for c in biz_cols if c != "business_id"])

        # Insert reviews (avoid duplicates on PK)
        existing_review_ids = set(k for (k,) in session.execute(text("SELECT review_id FROM reviews")).all())
        review_df = df[review_cols].drop_duplicates(subset=["review_id"])
        review_df = review_df[~review_df["review_id"].isin(existing_review_ids)]
        review_objs = []
        for rec in review_df.to_dict("records"):
            # Convert pandas Timestamp to python datetime
            if "created_at" in rec and pd.notna(rec["created_at"]):
                if isinstance(rec["created_at"], pd.Timestamp):
                    rec["created_at"] = rec["created_at"].to_pydatetime()
                elif isinstance(rec["created_at"], str):
                    rec["created_at"] = pd.to_datetime(rec["created_at"], errors="coerce", utc=True)
                    rec["created_at"] = None if pd.isna(rec["created_at"]) else rec["created_at"].to_pydatetime()
            review_objs.append(Review(**{k: (None if pd.isna(v) else v) for k, v in rec.items()}))
        if review_objs:
            session.add_all(review_objs)

        session.add(IngestMetadata(source_path=csv_path, total_rows=total_rows, loaded_rows=len(review_objs)))
        session.commit()
        print(f"Ingest complete. Rows in: {total_rows}, reviews loaded: {len(review_objs)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest reviews CSV into the database")
    parser.add_argument("--csv", required=True, help="Path to CSV (e.g., data/reviews.csv)")
    args = parser.parse_args()
    run(args.csv)
