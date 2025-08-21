import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

import reports


class TestReports:
    """Test cases for report generation functions"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        with tempfile.TemporaryDirectory() as temp_path:
            # Override the BASE path for testing
            original_base = reports.BASE
            reports.BASE = Path(temp_path)

            # Recreate the subdirectories
            reports.RESULTS = reports.BASE / "results"
            reports.ANALYTICS = reports.BASE / "analytics"
            reports.RESULTS.mkdir(exist_ok=True)
            reports.ANALYTICS.mkdir(exist_ok=True)

            yield temp_path

            # Restore original path
            reports.BASE = original_base
            reports.RESULTS = original_base / "results"
            reports.ANALYTICS = original_base / "analytics"

    def test_tail_lines_empty_file(self, temp_dir):
        """Test tail_lines with non-existent file"""
        result = reports.tail_lines(Path(temp_dir) / "nonexistent.log")
        assert result == []

    def test_tail_lines_with_data(self, temp_dir):
        """Test tail_lines with JSON data"""
        test_file = Path(temp_dir) / "test.log"
        test_data = [
            {"timestamp": 1, "status": "ok"},
            {"timestamp": 2, "status": "error"},
            {"timestamp": 3, "status": "ok"},
        ]

        with test_file.open("w") as f:
            for data in test_data:
                f.write(json.dumps(data) + "\n")

        result = reports.tail_lines(test_file, n=2)
        assert len(result) == 2
        assert result[0]["timestamp"] == 2
        assert result[1]["timestamp"] == 3

    def test_reports_for_cid(self, temp_dir):
        """Test reports_for_cid function"""
        cid = "test_cid_123"
        test_data = [
            {"timestamp": 1, "status": "ok", "response_time": 100},
            {"timestamp": 2, "status": "error", "error": "timeout"},
        ]

        # Create results file
        results_file = reports.RESULTS / f"{cid}.log"
        with results_file.open("w") as f:
            for data in test_data:
                f.write(json.dumps(data) + "\n")

        result = reports.reports_for_cid(cid)
        assert len(result) == 2
        assert result[0]["status"] == "ok"
        assert result[1]["status"] == "error"

    def test_timeseries_for_wid(self, temp_dir):
        """Test timeseries_for_wid function"""
        token = "test_token"
        wid = "test_wid_123"
        test_data = [
            {"timestamp": 1, "response_time": 150},
            {"timestamp": 2, "response_time": 200},
        ]

        # Create customer directory structure
        customer_dir = reports.BASE / "customers" / token / "watchers"
        customer_dir.mkdir(parents=True, exist_ok=True)

        watcher_file = customer_dir / f"{wid}.log"
        with watcher_file.open("w") as f:
            for data in test_data:
                f.write(json.dumps(data) + "\n")

        result = reports.timeseries_for_wid(token, wid)
        assert len(result) == 2
        assert result[0]["response_time"] == 150
        assert result[1]["response_time"] == 200

    def test_analytics_for_cid_exists(self, temp_dir):
        """Test analytics_for_cid when file exists"""
        cid = "test_cid_456"
        test_analytics = {
            "average_response_time": 125.5,
            "uptime_percentage": 99.2,
            "total_requests": 1000,
        }

        analytics_file = reports.ANALYTICS / f"{cid}.json"
        with analytics_file.open("w") as f:
            json.dump(test_analytics, f)

        result = reports.analytics_for_cid(cid)
        assert result == test_analytics

    def test_analytics_for_cid_not_exists(self, temp_dir):
        """Test analytics_for_cid when file doesn't exist"""
        cid = "nonexistent_cid"
        result = reports.analytics_for_cid(cid)
        assert result == {}

    def test_tail_lines_limit(self, temp_dir):
        """Test that tail_lines respects the limit parameter"""
        test_file = Path(temp_dir) / "test.log"
        test_data = [{"id": i} for i in range(10)]

        with test_file.open("w") as f:
            for data in test_data:
                f.write(json.dumps(data) + "\n")

        result = reports.tail_lines(test_file, n=3)
        assert len(result) == 3
        assert result[0]["id"] == 7  # Should get last 3 items
        assert result[1]["id"] == 8
        assert result[2]["id"] == 9
