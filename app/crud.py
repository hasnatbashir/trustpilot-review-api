from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.pii import mask_email
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

def to_expanded_review_dict(r: Review, u: User, b: Business, mask_pii: bool) -> dict:
    rd = sa_to_dict(r)
    ud = sa_to_dict(u)
    bd = sa_to_dict(b)

    # PII masking
    if mask_pii:
        if "email" in ud and ud["email"]:
            ud["email"] = mask_email(ud["email"])

    # Convert datetime to iso
    if "created_at" in rd and rd["created_at"]:
        rd["created_at"] = rd["created_at"].isoformat()

    combined = {**rd, **ud, **bd}
    return {k: combined.get(k) for k in HEADERS["reviews_expanded"]}