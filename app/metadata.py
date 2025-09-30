from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from .database import Base
from app.constants import TBL_INGEST_METADATA

class IngestMetadata(Base):
    __tablename__ = TBL_INGEST_METADATA
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    loaded_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False)  # SHA256 or similar
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
