from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.constants import F_CREATED_AT, F_EMAIL, F_IP, F_USER_NAME
from app.pii import mask_email, mask_ip, mask_name
from .models import Business, User, Review
from .utils import sa_to_dict
from .schemas import HEADERS

def query_reviews_by_business(
    db: Session, business_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
):
    stmt = select(Review).where(Review.business_id == business_id)
    if start_date:
        stmt = stmt.where(Review.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Review.created_at < end_date)
    if min_rating is not None:
        stmt = stmt.where(Review.rating >= min_rating)
    if max_rating is not None:
        stmt = stmt.where(Review.rating <= max_rating)
    stmt = stmt.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()

def query_reviews_by_user(
    db: Session, user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
):
    stmt = select(Review).where(Review.user_id == user_id)
    if start_date:
        stmt = stmt.where(Review.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Review.created_at < end_date)
    if min_rating is not None:
        stmt = stmt.where(Review.rating >= min_rating)
    if max_rating is not None:
        stmt = stmt.where(Review.rating <= max_rating)
    stmt = stmt.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()

def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.get(User, user_id)

def to_review_dict(r: Review) -> dict:
    row = sa_to_dict(r)
    # Convert datetime to isoformat string
    if "created_at" in row and row["created_at"]:
        row["created_at"] = row["created_at"].isoformat()
    # Only keep keys in HEADERS["reviews"] (or reviews_with_ip)
    return {k: row.get(k) for k in HEADERS["reviews"]}

def to_user_dict(u: User) -> dict:
    row = sa_to_dict(u)
    return {k: row.get(k) for k in HEADERS["users"]}

def to_expanded_review_dict(r, u, b, mask_pii: bool = True) -> dict:
    rd = sa_to_dict(r)
    ud = sa_to_dict(u)
    bd = sa_to_dict(b)

    # Convert datetime to iso
    if F_CREATED_AT in rd and rd[F_CREATED_AT]:
        rd[F_CREATED_AT] = rd[F_CREATED_AT].isoformat()

    combined = {**rd, **ud, **bd}

    # Apply PII masking
    if mask_pii:
        if F_EMAIL in combined:
            combined[F_EMAIL] = mask_email(combined[F_EMAIL])
        if F_USER_NAME in combined:
            combined[F_USER_NAME] = mask_name(combined[F_USER_NAME])
        if F_IP in combined:
            combined[F_IP] = mask_ip(combined[F_IP])

    return {k: combined.get(k) for k in HEADERS["reviews_expanded"]}