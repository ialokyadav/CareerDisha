import os
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from common.mongodb import get_db

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset_from_mongo():
    db = get_db()
    cursor = db["skill_training"].find({}, {"text": 1, "skills": 1})
    texts = []
    labels = []
    for doc in cursor:
        text = str(doc.get("text", "")).strip()
        skills = [s.strip().lower() for s in doc.get("skills", []) if str(s).strip()]
        if not text or not skills:
            continue
        texts.append(text)
        labels.append(skills)
    return texts, labels


def train():
    texts, labels = load_dataset_from_mongo()
    if not texts:
        raise ValueError("No training data found in MongoDB collection: skill_training")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
    X = vectorizer.fit_transform(texts)

    mlb = MultiLabelBinarizer()
    Y = mlb.fit_transform(labels)

    classifier = OneVsRestClassifier(LogisticRegression(max_iter=200))
    classifier.fit(X, Y)

    joblib.dump(vectorizer, MODEL_DIR / "skill_vectorizer.joblib")
    joblib.dump(mlb, MODEL_DIR / "skill_mlb.joblib")
    joblib.dump(classifier, MODEL_DIR / "skill_model.joblib")

    return {
        "skills": list(mlb.classes_),
        "num_samples": len(texts),
    }


if __name__ == "__main__":
    info = train()
    print(f"Trained skill extractor on {info['num_samples']} samples.")
    print(f"Skills: {info['skills']}")
