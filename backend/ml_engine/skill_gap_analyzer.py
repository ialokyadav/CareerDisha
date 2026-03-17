import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROLE_SKILLS_PATH = BASE_DIR / "datasets" / "role_skills.json"
DEPENDENCIES_PATH = BASE_DIR / "datasets" / "skill_dependencies.json"
CONFIG_PATH = BASE_DIR / "datasets" / "engine_config.json"

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)["skill_gap_analyzer"]
    except Exception:
        return {"weak_threshold": 0.7, "missing_threshold": 0.4}


from common.mongodb import get_db

def load_role_skills():
    with open(ROLE_SKILLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dependencies():
    with open(DEPENDENCIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_required_skills(role):
    """
    Fetches the most common skills for a role from MongoDB training data.
    Falls back to static JSON if no training data exists.
    """
    db = get_db()
    
    # Aggregation pipeline to find top skills for this role
    pipeline = [
        {"$match": {"role": role}},
        {"$unwind": "$skills"},
        # Normalize skill names (lowercase, strip)
        {"$project": {"skill": {"$toLower": {"$trim": {"input": "$skills"}}}}},
        {"$group": {"_id": "$skill", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 25}  # Top 25 most common skills
    ]
    
    try:
        results = list(db["role_training"].aggregate(pipeline))
        if results:
            # If we have data, return top skills
            return [r["_id"] for r in results]
    except Exception as e:
        print(f"Error fetching dynamic skills for {role}: {e}")
        
    # Fallback to static JSON
    static_skills = load_role_skills()
    return [s.lower() for s in static_skills.get(role, [])]


def analyze_skill_gap(extracted_skills, target_role, performance=None):
    required = get_required_skills(target_role)
    extracted = [s.lower() for s in extracted_skills]

    config = load_config()
    weak_threshold = config.get("weak_threshold", 0.7)

    matched = sorted(set(required) & set(extracted))
    missing = sorted(set(required) - set(extracted))

    weak = []
    if performance:
        for skill, accuracy in performance.items():
            if accuracy < weak_threshold and skill.lower() in required:
                weak.append(skill.lower())

    weak = sorted(set(weak))

    roadmap = generate_roadmap(target_role, missing, weak)

    return {
        "target_role": target_role,
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "weak_skills": weak,
        "roadmap": roadmap,
    }


def generate_roadmap(target_role, missing_skills, weak_skills):
    deps = load_dependencies()
    skill_map = {d["skill"].lower(): d for d in deps}
    all_gaps = list(dict.fromkeys([s.lower() for s in missing_skills + weak_skills]))

    phases = {"Foundation": [], "Core": [], "Advanced": []}

    for skill in all_gaps:
        meta = skill_map.get(skill, {
            "skill": skill,
            "prerequisite": [],
            "difficulty": "Medium",
            "eta_weeks": 2,
            "level": "Core",
        })
        entry = {
            "skill": meta["skill"],
            "prerequisite": meta.get("prerequisite", []),
            "difficulty": meta.get("difficulty", "Medium"),
            "eta_weeks": meta.get("eta_weeks", 2),
        }
        level = meta.get("level", "Core")
        if level not in phases:
            level = "Core"
        phases[level].append(entry)

    roadmap = {
        "target_role": target_role,
        "phases": [
            {"phase": "Foundation", "skills": phases["Foundation"]},
            {"phase": "Core", "skills": phases["Core"]},
            {"phase": "Advanced", "skills": phases["Advanced"]},
        ],
    }
    return roadmap
