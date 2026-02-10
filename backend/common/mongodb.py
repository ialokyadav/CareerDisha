import os
from pymongo import MongoClient
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_client = None


def get_client():
    global _client
    if _client is None:
        try:
            uri = getattr(settings, "MONGODB_URI", None)
        except ImproperlyConfigured:
            uri = None
        uri = uri or os.environ.get("MONGODB_URI")
        _client = MongoClient(uri)
    return _client


def get_db():
    client = get_client()
    try:
        db_name = getattr(settings, "MONGODB_DB", None)
    except ImproperlyConfigured:
        db_name = None
    db_name = db_name or os.environ.get("MONGODB_DB", "skill_assessment")
    return client[db_name]
