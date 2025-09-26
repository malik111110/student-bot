from __future__ import annotations

from typing import Optional
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from core.config import settings


_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is not None:
        return _client

    if not settings.MONGODB_URI:
        raise RuntimeError("MONGODB_URI is not configured in environment")

    # Use basic MongoDB client configuration
    # The SSL issues will be handled at the application level with fallback logging
    _client = MongoClient(
        settings.MONGODB_URI, 
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=5000,  # Quick timeout to fail fast
        connectTimeoutMS=10000,
        socketTimeoutMS=20000,
    )
    return _client


def get_db(db_name: str = "aspire_bot"):
    return get_mongo_client()[db_name]


