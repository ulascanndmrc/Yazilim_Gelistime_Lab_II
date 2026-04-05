"""
GREEN PHASE: Request logger implementation satisfying TDD tests.
Logs all traffic to MongoDB with full metadata.
"""
from datetime import datetime
from typing import Optional
from app.models import LogStatistics


class RequestLogger:
    """Logs every request/response through the Dispatcher to MongoDB."""

    def __init__(self, db):
        self._db = db

    def build_log_entry(
        self,
        method: str,
        path: str,
        user_id: Optional[str],
        target_service: str,
        status_code: int,
        response_time_ms: float,
        error: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Build a log entry dict (also used directly in tests)."""
        return {
            "method": method,
            "path": path,
            "user_id": user_id,
            "target_service": target_service,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.utcnow(),
            "error": error,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

    async def log_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str],
        target_service: str,
        status_code: int,
        response_time_ms: float,
        error: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Persist a log entry to MongoDB (fire-and-forget)."""
        entry = self.build_log_entry(
            method, path, user_id, target_service,
            status_code, response_time_ms, error, ip_address, user_agent
        )
        await self._db.logs.insert_one(entry)

    async def get_recent_logs(self, limit: int = 100) -> list:
        cursor = self._db.logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(limit)

    async def get_statistics(self) -> LogStatistics:
        pipeline = [{"$facet": {
            "total":   [{"$count": "count"}],
            "success": [{"$match": {"status_code": {"$gte": 200, "$lt": 400}}}, {"$count": "count"}],
            "errors":  [{"$match": {"status_code": {"$gte": 400}}}, {"$count": "count"}],
            "avg_time":[{"$group": {"_id": None, "avg": {"$avg": "$response_time_ms"}}}],
            "per_svc": [{"$group": {"_id": "$target_service", "count": {"$sum": 1}}}],
        }}]
        result = await self._db.logs.aggregate(pipeline).to_list(1)
        if not result:
            return LogStatistics(total_requests=0, success_count=0, error_count=0,
                                 avg_response_time_ms=0.0, requests_per_service={})
        r = result[0]
        total   = r["total"][0]["count"]   if r["total"]   else 0
        success = r["success"][0]["count"] if r["success"] else 0
        errors  = r["errors"][0]["count"]  if r["errors"]  else 0
        avg     = r["avg_time"][0]["avg"]  if r["avg_time"] else 0.0
        per_svc = {item["_id"]: item["count"] for item in r["per_svc"]}
        return LogStatistics(
            total_requests=total, success_count=success, error_count=errors,
            avg_response_time_ms=round(avg or 0.0, 2), requests_per_service=per_svc
        )
