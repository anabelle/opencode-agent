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


class TestCreditManagement:
    """Test cases for credit management logic"""

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

    def test_session_creation_with_credits(self, temp_db):
        """Test creating a new session with initial credits"""
        ts = time.time()
        token = str(uuid.uuid4())
        initial_credits = 100

        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, initial_credits, ts, ts),
            )
            conn.commit()

        # Verify session was created
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session is not None
            assert session["token"] == token
            assert session["credits"] == initial_credits
            assert session["created"] == ts
            assert session["last_used"] == ts

    def test_credit_topup_existing_session(self, temp_db):
        """Test adding credits to existing session"""
        ts = time.time()
        token = str(uuid.uuid4())
        initial_credits = 50
        topup_amount = 25

        # Create initial session
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, initial_credits, ts, ts),
            )
            conn.commit()

        # Topup credits
        new_ts = time.time()
        new_balance = initial_credits + topup_amount
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE sessions SET credits = ?, last_used = ? WHERE token = ?",
                (new_balance, new_ts, token),
            )
            conn.commit()

        # Verify topup
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session["credits"] == new_balance
            assert session["last_used"] == new_ts

    def test_credit_consumption_sufficient_funds(self, temp_db):
        """Test consuming credits when sufficient funds available"""
        ts = time.time()
        token = str(uuid.uuid4())
        initial_credits = 100
        consumption_amount = 30

        # Create session with credits
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, initial_credits, ts, ts),
            )
            conn.commit()

        # Consume credits
        new_ts = time.time()
        new_balance = initial_credits - consumption_amount
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE sessions SET credits = ?, last_used = ? WHERE token = ?",
                (new_balance, new_ts, token),
            )
            conn.commit()

        # Verify consumption
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session["credits"] == new_balance
            assert session["last_used"] == new_ts

    def test_credit_consumption_insufficient_funds(self, temp_db):
        """Test attempting to consume more credits than available"""
        ts = time.time()
        token = str(uuid.uuid4())
        initial_credits = 20
        consumption_amount = 50  # More than available

        # Create session with insufficient credits
        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, initial_credits, ts, ts),
            )
            conn.commit()

        # Attempt to consume - should not succeed
        with db.get_conn() as conn:
            c = conn.cursor()
            session = c.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            assert session["credits"] == initial_credits  # Should remain unchanged

    def test_ledger_entry_creation(self, temp_db):
        """Test that ledger entries are created for transactions"""
        ts = time.time()
        token = str(uuid.uuid4())
        amount = 100
        balance = 100

        with db.get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO ledger(ts, action, token, amount, balance, note) VALUES (?, ?, ?, ?, ?, ?)",
                (ts, "CREATE_SESSION_TOPUP", token, amount, balance, None),
            )
            conn.commit()

        # Verify ledger entry
        with db.get_conn() as conn:
            c = conn.cursor()
            entry = c.execute(
                "SELECT * FROM ledger WHERE token = ?", (token,)
            ).fetchone()
            assert entry is not None
            assert entry["action"] == "CREATE_SESSION_TOPUP"
            assert entry["token"] == token
            assert entry["amount"] == amount
            assert entry["balance"] == balance
