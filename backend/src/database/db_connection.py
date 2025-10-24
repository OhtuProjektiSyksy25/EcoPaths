"""
Database connection utilities for SQLAlchemy and PostGIS.

Handles engine creation, session setup, and environment loading.
"""

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import DatabaseConfig


BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = BASE_DIR / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f".env loaded from {dotenv_path}")
else:
    print(f"WARNING: .env not found at {dotenv_path}")

Base = declarative_base()


def get_engine():
    """
    Create and return a SQLAlchemy engine using database configuration.

    Returns:
        sqlalchemy.Engine: Engine connected to the configured database.
    """
    db_config = DatabaseConfig()
    return create_engine(db_config.connection_string, echo=False)


def get_session():
    """
    Create and return a SQLAlchemy session factory.

    Returns:
        sqlalchemy.orm.sessionmaker: Configured sessionmaker object.
    """
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session_instance():
    """
    Create and return a single active SQLAlchemy session instance.

    Returns:
        sqlalchemy.orm.Session: A database session.
    """
    session_local = get_session()
    return session_local()
