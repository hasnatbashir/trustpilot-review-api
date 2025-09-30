import pandas as pd

from app.constants import F_BUSINESS_ID, F_REVIEW_ID, F_USER_ID

def basic_validations(df: pd.DataFrame) -> None:
    """Perform basic, non-fatal validations and normalisations on an input DataFrame.

    The function mutates the provided DataFrame in-place for fixable issues.

    Args:
        df: pandas.DataFrame loaded from source CSV with normalized column names.

    Raises:
        ValueError: if required key columns are missing.
    """
    required = [F_REVIEW_ID, F_USER_ID, F_BUSINESS_ID]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if "rating" in df.columns:
        # Keep ratings within 1..5 (adjust if spec differs)
        bad = df[~df["rating"].fillna(0).between(1,5)]
        if len(bad) > 0:
            # Non-fatal: clamp values
            df.loc[~df["rating"].between(1,5), "rating"] = None
