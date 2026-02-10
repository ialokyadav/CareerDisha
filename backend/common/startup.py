import os
from pymongo.errors import ServerSelectionTimeoutError
from common.mongodb import get_client, get_db


def log_mongodb_status():
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGODB_DB", "skill_assessment")
    try:
        client = get_client()
        client.admin.command("ping")
        get_db()
        print(f"MongoDB connected at {uri} (db: {db_name})")
    except ServerSelectionTimeoutError:
        print(f"MongoDB connection failed at {uri} (db: {db_name})")
