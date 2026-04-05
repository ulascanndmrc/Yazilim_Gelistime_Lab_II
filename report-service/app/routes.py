from fastapi import APIRouter, HTTPException, Header
from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from app.models import ReportCreate, ReportResponse
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _verify_key(x_internal_api_key: Optional[str]) -> None:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Forbidden: direct access not allowed")


def _doc_to_response(doc: dict) -> ReportResponse:
    return ReportResponse(
        id=str(doc["_id"]),
        report_type=doc["report_type"],
        title=doc["title"],
        description=doc.get("description"),
        data=doc.get("data"),
        created_by=doc["created_by"],
        created_at=doc["created_at"],
    )


@router.get("")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50,
    x_internal_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    _verify_key(x_internal_api_key)
    db = get_db()
    query = {}
    if report_type:
        query["report_type"] = report_type
    cursor = db.reports.find(query, {"_id": 1, "report_type": 1,
                                     "title": 1, "description": 1,
                                     "created_by": 1, "created_at": 1}).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(limit)
    return [_doc_to_response(d) for d in docs]


@router.post("", status_code=201)
async def create_report(
    body: ReportCreate,
    x_internal_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    _verify_key(x_internal_api_key)
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    db = get_db()
    doc = {
        "report_type": body.report_type,
        "title": body.title,
        "description": body.description,
        "data": body.data,
        "created_by": x_user_id,
        "created_at": datetime.utcnow(),
    }
    result = await db.reports.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_response(doc)


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    x_internal_api_key: Optional[str] = Header(None),
):
    _verify_key(x_internal_api_key)
    db = get_db()
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid report ID")
    doc = await db.reports.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return _doc_to_response(doc)


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    x_internal_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    _verify_key(x_internal_api_key)
    db = get_db()
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid report ID")
    doc = await db.reports.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    if doc["created_by"] != x_user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's report")
    await db.reports.delete_one({"_id": oid})


@router.get("/summary/stats")
async def report_summary(x_internal_api_key: Optional[str] = Header(None)):
    _verify_key(x_internal_api_key)
    db = get_db()
    pipeline = [{"$group": {"_id": "$report_type", "count": {"$sum": 1}}}]
    result = await db.reports.aggregate(pipeline).to_list(100)
    total = await db.reports.count_documents({})
    return {
        "total_reports": total,
        "by_type": {item["_id"]: item["count"] for item in result}
    }
