from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)

    reviews = relationship("Review", back_populates="user")

class Business(Base):
    __tablename__ = "businesses"
    business_id: Mapped[str] = mapped_column(String, primary_key=True)
    business_name: Mapped[str | None] = mapped_column(String, nullable=True)

    reviews = relationship("Review", back_populates="business")

class Review(Base):
    __tablename__ = "reviews"
    review_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), index=True)
    business_id: Mapped[str] = mapped_column(String, ForeignKey("businesses.business_id"), index=True)

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reviews")
    business = relationship("Business", back_populates="reviews")
