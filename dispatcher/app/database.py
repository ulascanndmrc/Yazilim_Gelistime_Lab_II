from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client = None
_db = None


async def connect_to_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client.get_default_database()
    await _db.logs.create_index("timestamp")
    await _db.logs.create_index("user_id")
    await _db.logs.create_index("target_service")
    print("[Dispatcher] Connected to MongoDB")


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
