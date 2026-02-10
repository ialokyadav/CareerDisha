from datetime import datetime
from common.mongodb import get_db

COLLECTION = "performance_history"


def record_attempt(user_id, role, result, difficulty):
    db = get_db()
    doc = {
        "user_id": user_id,
        "role": role,
        "timestamp": datetime.utcnow(),
        "total": result["total"],
        "correct": result["correct"],
        "accuracy": result["accuracy"],
        "skill_stats": result["skill_stats"],
        "difficulty": difficulty,
    }
    inserted = db[COLLECTION].insert_one(doc)
    doc["_id"] = inserted.inserted_id
    return doc


def get_user_history(user_id, limit=20):
    db = get_db()
    cursor = db[COLLECTION].find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return list(cursor)


def get_skill_accuracy_summary(user_id):
    db = get_db()
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": {"path": "$skill_stats", "preserveNullAndEmptyArrays": True}},
    ]
    # Use client-side aggregation for simplicity
    history = list(db[COLLECTION].find({"user_id": user_id}))
    totals = {}
    for doc in history:
        for skill, stats in doc.get("skill_stats", {}).items():
            totals.setdefault(skill, {"correct": 0, "total": 0})
            totals[skill]["correct"] += stats.get("correct", 0)
            totals[skill]["total"] += stats.get("total", 0)

    accuracy = {}
    for skill, v in totals.items():
        accuracy[skill] = v["correct"] / v["total"] if v["total"] else 0.0
    return accuracy
