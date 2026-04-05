from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client = None
_db = None


async def connect_to_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client.get_default_database()
    await _db.users.create_index("email", unique=True)
    await _db.users.create_index("username", unique=True)
    print("[Login Service] Connected to MongoDB")


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
