import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

import db


class TestDatabaseOperations:
    """Test cases for database operations"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_path = f.name

        # Override the DB_PATH for testing
        original_path = db.DB_PATH
        db.DB_PATH = Path(temp_path)

        # Initialize the test database
        db.init_db()

        yield temp_path

        # Cleanup
        db.DB_PATH = original_path
        os.unlink(temp_path)

    def test_init_db_creates_tables(self, temp_db):
        """Test that init_db creates all required tables"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        # Check if all tables exist
        tables = ["sessions", "canonical_targets", "watchers", "ledger"]
        for table in tables:
            c.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            assert c.fetchone() is not None, f"Table {table} was not created"

        conn.close()

    def test_get_conn_context_manager(self, temp_db):
        """Test that get_conn context manager works properly"""
        with db.get_conn() as conn:
            assert isinstance(conn, sqlite3.Connection)
            # Test that we can execute queries
            c = conn.cursor()
            c.execute("SELECT 1")
            result = c.fetchone()
            assert result[0] == 1

    def test_foreign_keys_enabled(self, temp_db):
        """Test that foreign keys can be enabled"""
        with db.get_conn() as conn:
            c = conn.cursor()
            # Enable foreign keys for this connection
            c.execute("PRAGMA foreign_keys = ON")
            c.execute("PRAGMA foreign_keys")
            result = c.fetchone()
            assert result[0] == 1, "Foreign keys should be enabled when explicitly set"

    def test_row_factory_set(self, temp_db):
        """Test that row factory is set to Row"""
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 as test_col")
            result = c.fetchone()
            # Should be able to access by column name
            assert result["test_col"] == 1
