from pathlib import Path
import re
import joblib
import numpy as np
from common.utils import normalize_text

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
GLOBAL_SKILLS_PATH = BASE_DIR / "datasets" / "global_skills.txt"

ALIAS_MAP = {
    "js": "javascript",
    "reactjs": "react",
    "nodejs": "node.js",
    "sklearn": "scikit-learn",
    "oops python": "oop python",
    "oops c++": "oop c++",
    "ml algorithms": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "dbms": "database",
    "ci/cd": "cicd",
}


def _load_assets():
    vectorizer = joblib.load(MODEL_DIR / "skill_vectorizer.joblib")
    mlb = joblib.load(MODEL_DIR / "skill_mlb.joblib")
    model = joblib.load(MODEL_DIR / "skill_model.joblib")
    return vectorizer, mlb, model


def _load_global_skills():
    if not GLOBAL_SKILLS_PATH.exists():
        return []
    skills = []
    for line in GLOBAL_SKILLS_PATH.read_text(encoding="utf-8").splitlines():
        item = line.strip().lower()
        if item:
            canonical = ALIAS_MAP.get(item, item)
            skills.append(canonical)
    return list(dict.fromkeys(skills))


def _keyword_match(text: str):
    cleaned = normalize_text(text)
    skills = _load_global_skills()
    matches = []
    for skill in skills:
        pattern = r"\b" + re.escape(skill) + r"\b"
        count = len(re.findall(pattern, cleaned))
        if count:
            score = min(1.0, 0.2 * count + 0.6)
            matches.append((skill, score))
    return sorted(matches, key=lambda x: x[1], reverse=True)


def predict_skills(text: str, threshold: float = 0.35, top_k: int = 20):
    # Strict extraction: only skills mentioned in resume text.
    keyword_matches = _keyword_match(text)
    keyword_map = {skill: score for skill, score in keyword_matches}

    if not keyword_map:
        return []

    vectorizer, mlb, model = _load_assets()
    X = vectorizer.transform([text])
    probs = model.predict_proba(X)[0]

    merged = {}
    for idx, prob in enumerate(probs):
        skill = mlb.classes_[idx]
        if skill in keyword_map:
            merged[skill] = min(1.0, max(keyword_map[skill], float(prob)) + 0.15)

    for skill, score in keyword_map.items():
        if skill not in merged:
            merged[skill] = score

    ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


def predict_skills_with_suggestions(text: str, threshold: float = 0.35, top_k: int = 20, suggest_top_k: int = 10):
    # Extract only mentioned skills, but also return ML-only suggestions.
    keyword_matches = _keyword_match(text)
    keyword_set = {skill for skill, _ in keyword_matches}

    vectorizer, mlb, model = _load_assets()
    X = vectorizer.transform([text])
    probs = model.predict_proba(X)[0]

    extracted = predict_skills(text, threshold=threshold, top_k=top_k)

    suggestions = []
    idx_sorted = np.argsort(probs)[::-1]
    for idx in idx_sorted:
        skill = mlb.classes_[idx]
        if skill in keyword_set:
            continue
        suggestions.append((skill, float(probs[idx])))
        if len(suggestions) >= suggest_top_k:
            break

    return extracted, suggestions
