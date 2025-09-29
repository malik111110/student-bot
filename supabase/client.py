"""Simple Supabase client wrapper for this project.

This module provides a tiny helper to get a configured async Supabase client using
environment variables SUPABASE_URL and SUPABASE_KEY. It mirrors the project's
existing style of centralised settings in `core/config.py` but keeps a lightweight
helper here for data migrations and simple queries.

Note: This file depends on `supabase.client` from `supabase-py` (>=1.0.0).
"""

import os
from typing import Optional

from supabase import create_client  # type: ignore

_client = None


def get_client():
    """Return a singleton synchronous-ish Supabase client.

    The supabase-py client exposes both sync and async interfaces depending on
    usage. For simple migration scripts and lightweight usage we return the
    regular client. If you need full async support, adapt calls to
    client.postgrest.rpc/ etc. or use an async HTTP transport as documented by
    supabase-py.
    """
    global _client
    if _client is None:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client
