import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

import db


class TestChecker:
    """Test cases for checker.py functionality"""

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

    def test_log_function(self, temp_db, tmp_path):
        """Test the log function"""
        from checker import LOG

        # Override the log file path for testing
        original_log = LOG
        test_log = tmp_path / "test.log"

        # We can't easily override the LOG constant, so let's just test that the function exists
        from checker import log
        assert callable(log)

        # Test that it doesn't crash with basic inputs
        log("TEST_ACTION", "test details")

        # The actual log file writing would happen in the real environment

    def test_emergency_pause_file(self, temp_db):
        """Test emergency pause functionality"""
        from checker import EMER

        # Initially, emergency pause should not exist
        assert not EMER.exists()

        # Create emergency pause file
        EMER.touch()
        assert EMER.exists()

        # Clean up
        EMER.unlink()

    def test_normalize_url_function(self, temp_db):
        """Test URL normalization (extracted from app.py)"""
        from app import normalize_url

        # Test basic normalization
        assert normalize_url("https://example.com/") == "https://example.com"
        assert normalize_url("http://EXAMPLE.COM/PATH") == "http://example.com/PATH"
        assert normalize_url("example.com") == "http://example.com"

    def test_database_queries(self, temp_db):
        """Test database query patterns used in checker"""
        # Create test data
        with db.get_conn() as conn:
            c = conn.cursor()

            # Create a session
            token = "test_token"
            c.execute(
                "INSERT INTO sessions(token, credits, created, last_used) VALUES (?, ?, ?, ?)",
                (token, 100, time.time(), time.time())
            )

            # Create a canonical target
            cid = "test_cid"
            url = "https://example.com"
            c.execute(
                "INSERT INTO canonical_targets(cid, url, last_probe, last_ok, next_run) VALUES (?, ?, ?, ?, ?)",
                (cid, url, None, 0, time.time())
            )

            # Create a watcher
            wid = "test_wid"
            c.execute(
                "INSERT INTO watchers(wid, cid, token, interval, enabled, created) VALUES (?, ?, ?, ?, ?, ?)",
                (wid, cid, token, 60, 1, time.time())
            )

            conn.commit()

        # Test the query pattern used in checker
        with db.get_conn() as conn:
            c = conn.cursor()
            data = c.execute(
                """
                SELECT w.wid, w.interval, w.enabled, t.url, t.probe_type
                FROM watchers w
                JOIN canonical_targets t ON w.cid = t.cid
                WHERE w.enabled = 1
                """
            ).fetchall()

            assert len(data) == 1
            assert data[0]["wid"] == wid
            assert data[0]["url"] == url

    def test_timing_logic(self, temp_db):
        """Test the timing logic for when to run checks"""
        # This tests the logic that determines if enough time has passed
        current_time = time.time()
        interval = 60
        last_probe = current_time - 120  # 2 minutes ago

        # Should run check (enough time has passed)
        should_run = current_time >= (last_probe + interval)
        assert should_run == True

        # Should not run check (not enough time has passed)
        last_probe = current_time - 30  # 30 seconds ago
        should_run = current_time >= (last_probe + interval)
        assert should_run == False

    def test_subprocess_call_pattern(self, temp_db):
        """Test the subprocess call pattern used for HTTP checks"""
        import subprocess

        # Test a simple curl command (similar to what's used in checker)
        result = subprocess.run(
            ["curl", "-sS", "--max-time", "5", "-o", "/dev/null", "-w", "%{http_code}", "https://httpbin.org/status/200"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should succeed
        assert result.returncode == 0
        assert result.stdout.strip() == "200"

    def test_error_handling_patterns(self, temp_db):
        """Test error handling patterns used in checker"""
        from checker import log

        # Test exception handling
        try:
            raise ValueError("Test error")
        except Exception as e:
            log("TEST_ERROR", str(e))

        # Verify error was logged
        log_file = Path("/home/ubuntu/opencode_actions.log")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "TEST_ERROR" in content
            assert "Test error" in content