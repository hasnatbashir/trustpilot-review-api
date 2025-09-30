from sqlalchemy import create_engine
from .config import DATABASE_URL
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency generator that yields a SQLAlchemy Session.

    Usage:
        as a FastAPI dependency: db: Session = Depends(get_db)

    Yields:
        sqlalchemy.orm.Session: a database session that will be closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
