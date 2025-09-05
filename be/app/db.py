from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client: MongoClient | None = None
_db: Any | None = None


def get_db():
    global _client, _db
    if _db is not None:
        return _db
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27018")
    dbname = os.getenv("MONGODB_DB", "apms")
    _client = MongoClient(uri)
    _db = _client[dbname]
    return _db


def close_db():
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None

