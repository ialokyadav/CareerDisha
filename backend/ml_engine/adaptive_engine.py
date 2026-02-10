import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "datasets" / "engine_config.json"

DIFFICULTIES = ["Easy", "Medium", "Hard"]

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)["adaptive_engine"]
    except Exception:
        return {"upgrade_threshold": 0.8, "downgrade_threshold": 0.5}

def adjust_difficulty(accuracy: float, current: str) -> str:
    config = load_config()
    upgrade = config.get("upgrade_threshold", 0.8)
    downgrade = config.get("downgrade_threshold", 0.5)
    current = current.capitalize()
    if current not in DIFFICULTIES:
        current = "Medium"

    idx = DIFFICULTIES.index(current)

    idx = DIFFICULTIES.index(current)

    if accuracy >= upgrade and idx < len(DIFFICULTIES) - 1:
        return DIFFICULTIES[idx + 1]
    if accuracy <= downgrade and idx > 0:
        return DIFFICULTIES[idx - 1]
    return current


def aggregate_skill_accuracy(attempts):
    # attempts: list of {skill, correct, total}
    totals = {}
    for a in attempts:
        skill = a["skill"].lower()
        totals.setdefault(skill, {"correct": 0, "total": 0})
        totals[skill]["correct"] += a["correct"]
        totals[skill]["total"] += a["total"]

    accuracy = {}
    for skill, v in totals.items():
        accuracy[skill] = v["correct"] / v["total"] if v["total"] else 0.0
    return accuracy
