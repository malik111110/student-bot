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
    _client = MongoClient(
        settings.MONGODB_URI, 
        serverSelectionTimeoutMS=5000,  # Quick timeout to fail fast
        connectTimeoutMS=10000,
        socketTimeoutMS=20000,
        # SSL/TLS configuration for macOS compatibility
        # Add TLS kwargs only when explicitly enabled (e.g. via settings flag or URI options)
        **(
            dict(
                tls=True,
                tlsAllowInvalidCertificates=False,
                tlsAllowInvalidHostnames=False,
            )
            if settings.ENABLE_MONGODB_TLS
            else {}
        ),
        # Retry configuration
        retryWrites=True,
        retryReads=True,
        maxPoolSize=10,
        minPoolSize=1,
    )
    return _client


def get_db(db_name: str = "aspire_bot"):
    return get_mongo_client()[db_name]


