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

    # Enhanced MongoDB client configuration for macOS SSL compatibility
    client_kwargs = {
        "serverSelectionTimeoutMS": 5000,  # Quick timeout to fail fast
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 20000,
        "retryWrites": True,
        "retryReads": True,
        "maxPoolSize": 10,
        "minPoolSize": 1,
    }

    # Add TLS configuration if needed (for production MongoDB Atlas connections)
    if "mongodb+srv://" in settings.MONGODB_URI or getattr(
        settings, "ENABLE_MONGODB_TLS", False
    ):
        client_kwargs.update(
            {
                "tls": True,
                "tlsAllowInvalidCertificates": False,
                "tlsAllowInvalidHostnames": False,
            }
        )

    _client = MongoClient(settings.MONGODB_URI, **client_kwargs)
    return _client


def get_db(db_name: str = "aspire_bot"):
    return get_mongo_client()[db_name]
