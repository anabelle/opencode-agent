import os
import sqlite3
import sys
import tempfile
import time
import uuid
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

import db


class TestSessionManagement:
    """Test cases for session management and validation"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            temp_path = f.name

        original_path = db.DB_PATH
        db.DB_PATH = Path(temp_path)
        db.init_db()

        yield temp_path

        db.DB_PATH = original_path
        os.unlink(temp_path)

    def test_valid_session_exists(self, temp_db):
        """Test checking if a valid session exists"""
        ts = time.time()
        token = str(uuid.uuid4())

        # Create a session
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 100, ts, ts),
            )
            conn.commit()

        # Check if session exists
        with db.get_conn() as conn:
            c = conn.cursor()
            result = c.execute(
                "SELECT 1 FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert result is not None
            assert result[0] == 1

    def test_invalid_session_not_exists(self, temp_db):
        """Test checking if an invalid session doesn't exist"""
        fake_token = str(uuid.uuid4())

        with db.get_conn() as conn:
            c = conn.cursor()
            result = c.execute(
                "SELECT 1 FROM sessions WHERE token = ?", (fake_token,)
            ).fetchone()
            assert result is None

    def test_session_with_zero_credits(self, temp_db):
        """Test session with zero credits"""
        ts = time.time()
        token = str(uuid.uuid4())

        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 0, ts, ts),
            )
            conn.commit()

        # Verify session exists but has zero credits
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session is not None
            assert session["credits"] == 0

    def test_session_last_used_update(self, temp_db):
        """Test updating last_used timestamp"""
        ts = time.time()
        token = str(uuid.uuid4())

        # Create session
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 100, ts, ts),
            )
            conn.commit()

        # Update last_used
        new_ts = time.time()
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE sessions SET last_used = ? WHERE token = ?", (new_ts, token)
            )
            conn.commit()

        # Verify update
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session["last_used"] == new_ts

    def test_multiple_sessions(self, temp_db):
        """Test managing multiple sessions"""
        ts = time.time()
        tokens = [str(uuid.uuid4()) for _ in range(3)]

        # Create multiple sessions
        with db.get_conn() as conn:
            c = conn.cursor()
            for i, token in enumerate(tokens):
                c.execute(
                    "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                    (token, (i + 1) * 50, ts, ts),
                )
            conn.commit()

        # Verify all sessions exist
        with db.get_conn() as conn:
            c = conn.cursor()
            sessions = c.execute("SELECT * FROM sessions ORDER BY credits").fetchall()
            assert len(sessions) == 3
            assert sessions[0]["credits"] == 50
            assert sessions[1]["credits"] == 100
            assert sessions[2]["credits"] == 150

    def test_session_with_watchers(self, temp_db):
        """Test session with associated watchers"""
        ts = time.time()
        token = str(uuid.uuid4())
        url = "https://example.com"
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))

        # Create session
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 100, ts, ts),
            )
            # Create canonical target
            c.execute(
                "INSERT INTO canonical_targets(cid, url, last_probe, last_ok, next_run) VALUES (?, ?, ?, ?, ?)",
                (cid, url, None, 0, ts),
            )
            # Create watcher
            wid = str(int(time.time() * 1000))
            c.execute(
                "INSERT INTO watchers(wid, cid, token, interval, enabled, created) VALUES (?, ?, ?, ?, ?, ?)",
                (wid, cid, token, 60, 1, ts),
            )
            conn.commit()

        # Verify session and watcher relationship
        with db.get_conn() as conn:
            c = conn.cursor()
            watchers = c.execute(
                """
                SELECT w.wid, t.url
                FROM watchers w
                JOIN canonical_targets t ON w.cid = t.cid
                WHERE w.token = ?
            """,
                (token,),
            ).fetchall()

            assert len(watchers) == 1
            assert watchers[0]["wid"] == wid
            assert watchers[0]["url"] == url

    def test_session_deletion_cascades(self, temp_db):
        """Test that deleting a session cascades to related records when foreign keys are enabled"""
        ts = time.time()
        token = str(uuid.uuid4())
        url = "https://example.com"
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))

        # Create session with watcher
        with db.get_conn() as conn:
            c = conn.cursor()
            # Enable foreign keys for this test
            c.execute("PRAGMA foreign_keys = ON")
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 100, ts, ts),
            )
            c.execute(
                "INSERT INTO canonical_targets(cid, url, last_probe, last_ok, next_run) VALUES (?, ?, ?, ?, ?)",
                (cid, url, None, 0, ts),
            )
            wid = str(int(time.time() * 1000))
            c.execute(
                "INSERT INTO watchers(wid, cid, token, interval, enabled, created) VALUES (?, ?, ?, ?, ?, ?)",
                (wid, cid, token, 60, 1, ts),
            )
            conn.commit()

        # Delete session with foreign keys enabled
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute("PRAGMA foreign_keys = ON")
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

        # Verify watcher is also deleted (cascade)
        with db.get_conn() as conn:
            c = conn.cursor()
            watcher = c.execute(
                "SELECT * FROM watchers WHERE token = ?", (token,)
            ).fetchone()
            assert watcher is None
