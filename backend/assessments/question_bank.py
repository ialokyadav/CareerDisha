from common.mongodb import get_db

COLLECTION = "question_bank"


def seed_questions(questions):
    db = get_db()
    if not questions:
        return 0
    result = db[COLLECTION].insert_many(questions)
    return len(result.inserted_ids)


def find_questions(skills, difficulty, limit=10):
    db = get_db()
    query = {
        "skill": {"$in": skills},
        "difficulty": difficulty,
    }
    cursor = db[COLLECTION].find(query).limit(limit)
    return list(cursor)


def list_questions(skill=None, difficulty=None, limit=50):
    db = get_db()
    query = {}
    if skill:
        query["skill"] = skill
    if difficulty:
        query["difficulty"] = difficulty
    return list(db[COLLECTION].find(query).limit(limit))
