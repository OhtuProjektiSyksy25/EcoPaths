# tests/unit/database/test_db_connection.py
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import DeclarativeMeta
from src.database import db_connection


@patch("src.database.db_connection.DatabaseConfig")
@patch("src.database.db_connection.create_engine")
def test_get_engine_returns_engine(mock_create_engine, mock_config):
    mock_config.return_value.connection_string = "postgresql://user:pass@localhost/db"
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    engine = db_connection.get_engine()
    mock_create_engine.assert_called_once_with(
        "postgresql://user:pass@localhost/db", echo=False)
    assert engine == mock_engine


@patch("src.database.db_connection.get_engine")
def test_get_session_returns_sessionmaker(mock_engine):
    mock_engine.return_value = MagicMock()
    session_factory = db_connection.get_session()
    assert callable(session_factory)
    session = session_factory()
    assert hasattr(session, "commit")
    assert hasattr(session, "close")


@patch("src.database.db_connection.get_session")
def test_get_session_instance_returns_session(mock_session):
    mock_session_local = MagicMock()
    mock_session.return_value = lambda: mock_session_local

    session = db_connection.get_session_instance()
    assert session == mock_session_local


def test_base_is_declarative():
    assert isinstance(db_connection.Base, DeclarativeMeta)
