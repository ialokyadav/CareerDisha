from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from common.mongodb import get_db

ALLOWED_ROLES = [
    "Software Developer",
    "Web Developer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "Cloud Engineer",
    "DevOps Engineer",
    "Cyber Security Analyst",
    "Mobile App Developer",
    "System Engineer",
]

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

def train_role_model():
    skills_list = []
    roles = []
    db = get_db()
    cursor = db["role_training"].find({}, {"skills": 1, "role": 1})
    for doc in cursor:
        # Join skills with pipes to treat them as atomic units: |react|node.js|data analysis|
        skills = "|" + "|".join([s.strip().lower() for s in doc.get("skills", []) if str(s).strip()]) + "|"
        role = str(doc.get("role", "")).strip()
        if role not in ALLOWED_ROLES or len(skills) < 3:
            continue
        skills_list.append(skills)
        roles.append(role)

    if not roles:
        raise ValueError("No training data found in MongoDB collection: role_training")

    # Treat each skill between pipes as a single token
    vectorizer = TfidfVectorizer(token_pattern=r"[^|]+")
    X = vectorizer.fit_transform(skills_list)
    y = np.array(roles)

    # Split for validation to monitor bias
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Higher capacity model with regularization (min_samples_leaf)
    model = RandomForestClassifier(
        n_estimators=500, 
        min_samples_leaf=2, 
        random_state=42, 
        class_weight="balanced",
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Print diagnostics
    y_pred = model.predict(X_test)
    print("\n--- Training Diagnostics (Validation Set) ---")
    print(classification_report(y_test, y_pred))

    # Re-fit on full data for production
    model.fit(X, y)

    joblib.dump(vectorizer, MODEL_DIR / "role_vectorizer.joblib")
    joblib.dump(model, MODEL_DIR / "role_model.joblib")

    return {
        "num_samples": len(roles),
        "roles": sorted(set(roles)),
    }


def _load_assets():
    vectorizer = joblib.load(MODEL_DIR / "role_vectorizer.joblib")
    model = joblib.load(MODEL_DIR / "role_model.joblib")
    return vectorizer, model


def predict_role(skills):
    vectorizer, model = _load_assets()
    # Join skills with pipes for consistent prediction: |python|sql|
    text = "|" + "|".join([s.lower() for s in skills]) + "|"
    X = vectorizer.transform([text])

    proba = model.predict_proba(X)[0]
    idx = int(np.argmax(proba))
    role = model.classes_[idx]
    confidence = float(proba[idx])
    return role, confidence


if __name__ == "__main__":
    info = train_role_model()
    print(f"Trained role predictor on {info['num_samples']} samples.")
    print(f"Roles: {info['roles']}")
