"""
TDD - RED PHASE: Request logging tests for the Dispatcher.
Written BEFORE implementation (Red-Green-Refactor cycle).
File created: dispatcher/tests/test_logging.py  <-- BEFORE dispatcher/app/logger.py
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestRequestLogger:

    def test_log_entry_has_all_required_fields(self):
        from app.logger import RequestLogger
        logger = RequestLogger(db=MagicMock())
        entry = logger.build_log_entry(
            method="GET",
            path="/api/messages",
            user_id="user123",
            target_service="message-service",
            status_code=200,
            response_time_ms=45.2
        )
        required_fields = ["method", "path", "user_id", "target_service",
                           "status_code", "response_time_ms", "timestamp"]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

    def test_log_entry_timestamp_is_datetime(self):
        from app.logger import RequestLogger
        logger = RequestLogger(db=MagicMock())
        entry = logger.build_log_entry(
            method="POST", path="/auth/login", user_id=None,
            target_service="login-service", status_code=200, response_time_ms=10.0
        )
        assert isinstance(entry["timestamp"], datetime)

    def test_log_entry_captures_502_error(self):
        from app.logger import RequestLogger
        logger = RequestLogger(db=MagicMock())
        entry = logger.build_log_entry(
            method="GET", path="/api/messages", user_id="u1",
            target_service="message-service", status_code=502,
            response_time_ms=5000.0, error="Connection refused"
        )
        assert entry["status_code"] == 502
        assert entry["error"] == "Connection refused"

    def test_log_entry_anonymous_user(self):
        from app.logger import RequestLogger
        logger = RequestLogger(db=MagicMock())
        entry = logger.build_log_entry(
            method="POST", path="/auth/login", user_id=None,
            target_service="login-service", status_code=200, response_time_ms=5.0
        )
        assert entry["user_id"] is None

    def test_log_entry_stores_ip_and_user_agent(self):
        from app.logger import RequestLogger
        logger = RequestLogger(db=MagicMock())
        entry = logger.build_log_entry(
            method="GET", path="/api/users", user_id="u1",
            target_service="user-service", status_code=200,
            response_time_ms=12.0, ip_address="127.0.0.1",
            user_agent="Mozilla/5.0"
        )
        assert entry["ip_address"] == "127.0.0.1"
        assert entry["user_agent"] == "Mozilla/5.0"


class TestLogStatistics:

    def test_statistics_model_fields(self):
        from app.logger import LogStatistics
        stats = LogStatistics(
            total_requests=500,
            success_count=480,
            error_count=20,
            avg_response_time_ms=67.4,
            requests_per_service={"message-service": 200, "user-service": 150}
        )
        assert stats.total_requests == 500
        assert stats.success_count == 480
        assert stats.error_count == 20
        assert stats.avg_response_time_ms == 67.4
        assert stats.requests_per_service["message-service"] == 200

    def test_zero_statistics(self):
        from app.logger import LogStatistics
        stats = LogStatistics(
            total_requests=0, success_count=0, error_count=0,
            avg_response_time_ms=0.0, requests_per_service={}
        )
        assert stats.total_requests == 0
