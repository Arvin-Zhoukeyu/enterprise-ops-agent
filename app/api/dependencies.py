from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Create one database session for each API request.

    The session is always closed after the request
    finishes, even if an exception occurs.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()