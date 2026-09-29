from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine


def check_database() -> bool:
    """Check whether the application can reach the database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
