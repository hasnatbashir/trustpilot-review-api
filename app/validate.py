import pandas as pd

def basic_validations(df: pd.DataFrame) -> None:
    required = ["review_id", "user_id", "business_id"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if "rating" in df.columns:
        # Keep ratings within 1..5 (adjust if spec differs)
        bad = df[~df["rating"].fillna(0).between(1,5)]
        if len(bad) > 0:
            # Non-fatal: clamp values
            df.loc[~df["rating"].between(1,5), "rating"] = None
