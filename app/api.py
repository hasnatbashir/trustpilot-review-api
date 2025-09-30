from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import csv, io
from datetime import date
from typing import Optional, Annotated

from app.models import Business, Review, User
from app.schemas import HEADERS
from .database import get_db
from .crud import query_reviews_by_business, query_reviews_by_user, get_user, to_expanded_review_dict, to_review_dict, to_user_dict
from .pii import mask_row

router = APIRouter()

def stream_csv(dict_rows, headers, filename: str):
    """Stream an iterable of dict rows as a CSV HTTP response.

    Args:
        dict_rows: Iterable of dict-like rows (order implied by `headers`).
        headers: List of column names (fieldnames for CSV DictWriter).
        filename: Suggested filename included in Content-Disposition header.

    Returns:
        fastapi.responses.StreamingResponse streaming CSV bytes/text.
    """
    def iter_rows():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)
        for row in dict_rows:
            writer.writerow(row)
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)

    return StreamingResponse(
        iter_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

def validate_review_filters(
    min_rating: Annotated[Optional[int], Query(ge=1, le=5)] = None,
    max_rating: Annotated[Optional[int], Query(ge=1, le=5)] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Validate and normalise common query parameters used by review endpoints.

    Args:
        min_rating: Optional minimum rating (1..5).
        max_rating: Optional maximum rating (1..5).
        start_date: Optional inclusive start date.
        end_date: Optional exclusive end date.
        limit: Pagination limit (1..1000).
        offset: Pagination offset (>=0).

    Returns:
        dict: normalised filter values.
    """
    if min_rating is not None and max_rating is not None and min_rating > max_rating:
        raise HTTPException(status_code=422, detail="min_rating cannot exceed max_rating")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date cannot exceed end_date")
    return {
        "min_rating": min_rating,
        "max_rating": max_rating,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "offset": offset,
    }

@router.get("/health")
def health():
    """Healthcheck endpoint.

    Returns:
        dict: simple status payload.
    """
    return {"status": "ok"}

@router.get("/reviews/business/{business_id}")
def reviews_for_business(
    business_id: str,
    filters: dict = Depends(validate_review_filters),
    db: Session = Depends(get_db),
):
    """Return narrow (normalized) CSV extract of reviews for a business.

    Args:
        business_id: business identifier path param.
        filters: dependency-provided dict of filter values.
        db: DB session dependency.

    Returns:
        StreamingResponse: CSV response of rows matching HEADERS['reviews'].
    """
    items = query_reviews_by_business(
        db,
        business_id,
        filters["start_date"],
        filters["end_date"],
        filters["min_rating"],
        filters["max_rating"],
        filters["limit"],
        filters["offset"],
    )
    dicts = [to_review_dict(x) for x in items]
    return stream_csv(dicts, HEADERS["reviews"], f"reviews_business_{business_id}.csv")

@router.get("/reviews/user/{user_id}")
def reviews_by_user(
    user_id: str,
    filters: dict = Depends(validate_review_filters),
    db: Session = Depends(get_db),
):
    """Return narrow (normalized) CSV extract of reviews for a user.

    Args:
        user_id: user identifier path param.
        filters: dependency-provided dict of filter values.
        db: DB session dependency.

    Returns:
        StreamingResponse: CSV response of rows matching HEADERS['reviews'].
    """
    items = query_reviews_by_user(
        db,
        user_id,
        filters["start_date"],
        filters["end_date"],
        filters["min_rating"],
        filters["max_rating"],
        filters["limit"],
        filters["offset"],
    )
    dicts = [to_review_dict(x) for x in items]
    return stream_csv(dicts, HEADERS["reviews"], f"reviews_user_{user_id}.csv")

@router.get("/users/{user_id}")
def user_info(user_id: str, db: Session = Depends(get_db)):
    """Return a single-user CSV row (masked PII by default).

    Args:
        user_id: user identifier path param.
        db: DB session dependency.

    Returns:
        StreamingResponse: CSV with a single row matching HEADERS['users'].
    """
    u = get_user(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    row = mask_row(to_user_dict(u))
    return stream_csv([row], HEADERS["users"], f"user_{user_id}.csv")

@router.get("/reviews/business/{business_id}/expanded")
def reviews_for_business_expanded(
    business_id: str,
    mask_pii: bool = True,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Return expanded (joined) CSV extract of reviews for a business.

    Args:
        business_id: business identifier path param.
        mask_pii: whether to mask PII fields (default True).
        limit: pagination limit.
        offset: pagination offset.
        db: DB session dependency.

    Returns:
        StreamingResponse: CSV with columns HEADERS['reviews_expanded'].
    """
    q = (
        db.query(Review, User, Business)
        .join(User, Review.user_id == User.user_id)
        .join(Business, Review.business_id == Business.business_id)
        .filter(Review.business_id == business_id)
        .offset(offset).limit(limit).all()
    )
    dicts = [to_expanded_review_dict(r, u, b, mask_pii) for r, u, b in q]
    return stream_csv(dicts, HEADERS["reviews_expanded"], f"reviews_business_{business_id}_expanded.csv")


@router.get("/reviews/user/{user_id}/expanded")
def reviews_by_user_expanded(
    user_id: str,
    mask_pii: bool = True,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Return expanded (joined) CSV extract of reviews for a user.

    Args:
        user_id: user identifier path param.
        mask_pii: whether to mask PII fields (default True).
        limit: pagination limit.
        offset: pagination offset.
        db: DB session dependency.

    Returns:
        StreamingResponse: CSV with columns HEADERS['reviews_expanded'].
    """
    q = (
        db.query(Review, User, Business)
        .join(User, Review.user_id == User.user_id)
        .join(Business, Review.business_id == Business.business_id)
        .filter(Review.user_id == user_id)
        .offset(offset).limit(limit).all()
    )
    dicts = [to_expanded_review_dict(r, u, b, mask_pii) for r, u, b in q]
    return stream_csv(dicts, HEADERS["reviews_expanded"], f"reviews_user_{user_id}_expanded.csv")
