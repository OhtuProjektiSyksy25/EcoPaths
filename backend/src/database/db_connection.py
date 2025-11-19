"""
Database connection utilities for SQLAlchemy and PostGIS.

Handles engine creation, session setup, and environment loading.
"""

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config.settings import DatabaseConfig
from src.logger.logger import log

# ENVIRONMENT SETUP
BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = BASE_DIR / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path)
    log.debug(
        f".env loaded from {dotenv_path}", path=str(dotenv_path))
else:
    log.warning(
        f".env not found at {dotenv_path}", path=str(dotenv_path))


# DECLARATIVE BASE (SQLAlchemy 2.x)
class Base(DeclarativeBase):
    """Base class for all ORM models."""


# ENGINE AND SESSION FACTORIES


def get_engine(echo: bool = False):
    """
    Create and return a SQLAlchemy Engine instance.

    Args:
        echo (bool, optional): If True, logs SQL statements. Defaults to False.

    Returns:
        sqlalchemy.Engine: Configured database engine.
    """
    db_config = DatabaseConfig()
    return create_engine(db_config.connection_string, echo=echo, future=True)


def get_session():
    """
    Return a SQLAlchemy session factory bound to the engine.

    Returns:
        sessionmaker: Configured SQLAlchemy sessionmaker.
    """
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def get_session_instance():
    """
    Create and return a single active SQLAlchemy session instance.

    Returns:
        sqlalchemy.orm.Session: A database session.
    """
    session_local = get_session()
    return session_local()
