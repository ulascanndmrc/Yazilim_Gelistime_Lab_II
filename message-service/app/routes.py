from fastapi import APIRouter, HTTPException, Depends, Header
from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from app.models import MessageCreate, MessageUpdate, MessageResponse
from app.database import get_db
from app.middleware import verify_internal_key

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _doc_to_response(doc: dict) -> MessageResponse:
    return MessageResponse(
        id=str(doc["_id"]),
        content=doc["content"],
        sender_id=doc["sender_id"],
        recipient_id=doc.get("recipient_id"),
        channel=doc.get("channel", "general"),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),
    )


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "message-service"}


@router.get("", dependencies=[Depends(verify_internal_key)])
async def list_messages(
    channel: Optional[str] = None,
    limit: int = 50,
    x_user_id: Optional[str] = Header(None),
):
    db = get_db()
    query = {}
    if channel:
        query["channel"] = channel
    cursor = db.messages.find(query).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(limit)
    return [_doc_to_response(d) for d in docs]


@router.post("", status_code=201, dependencies=[Depends(verify_internal_key)])
async def create_message(
    body: MessageCreate,
    x_user_id: Optional[str] = Header(None),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    db = get_db()
    now = datetime.utcnow()
    doc = {
        "content": body.content,
        "sender_id": x_user_id,
        "recipient_id": body.recipient_id,
        "channel": body.channel,
        "created_at": now,
    }
    result = await db.messages.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_response(doc)


@router.get("/{message_id}", dependencies=[Depends(verify_internal_key)])
async def get_message(message_id: str):
    db = get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid message ID")
    doc = await db.messages.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Message not found")
    return _doc_to_response(doc)


@router.put("/{message_id}", dependencies=[Depends(verify_internal_key)])
async def update_message(
    message_id: str,
    body: MessageUpdate,
    x_user_id: Optional[str] = Header(None),
):
    db = get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid message ID")
    doc = await db.messages.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Message not found")
    if doc["sender_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's message")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow()
    await db.messages.update_one({"_id": oid}, {"$set": updates})
    doc.update(updates)
    return _doc_to_response(doc)


@router.delete("/{message_id}", status_code=204, dependencies=[Depends(verify_internal_key)])
async def delete_message(
    message_id: str,
    x_user_id: Optional[str] = Header(None),
):
    db = get_db()
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid message ID")
    doc = await db.messages.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Message not found")
    if doc["sender_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")
    await db.messages.delete_one({"_id": oid})
