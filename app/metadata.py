from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from .database import Base

class IngestMetadata(Base):
    __tablename__ = "ingest_metadata"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    loaded_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
