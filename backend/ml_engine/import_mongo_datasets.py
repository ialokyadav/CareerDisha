import csv
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from docx import Document
from common.mongodb import get_db

django.setup()

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

ROLE_ALIASES = {
    "software developer": "Software Developer",
    "web developer": "Web Developer",
    "backend developer": "Backend Developer",
    "backend engineer": "Backend Developer",
    "frontend developer": "Frontend Developer",
    "front end developer": "Frontend Developer",
    "full stack developer": "Full Stack Developer",
    "fullstack developer": "Full Stack Developer",
    "data scientist": "Data Scientist",
    "data analyst": "Data Analyst",
    "machine learning engineer": "Machine Learning Engineer",
    "ml engineer": "Machine Learning Engineer",
    "ai engineer": "AI Engineer",
    "business analyst": "Business Analyst",
    "cloud engineer": "Cloud Engineer",
    "cloud architect": "Cloud Engineer",
    "devops engineer": "DevOps Engineer",
    "cyber security analyst": "Cyber Security Analyst",
    "cybersecurity analyst": "Cyber Security Analyst",
    "cybersecurity expert": "Cyber Security Analyst",
    "cyber security expert": "Cyber Security Analyst",
    "mobile app developer": "Mobile App Developer",
    "android developer": "Mobile App Developer",
    "system engineer": "System Engineer",
}

TEXT_KEYS = [
    "resume",
    "resume_text",
    "summary",
    "description",
    "job_description",
    "text",
    "job_summary",
    "profile",
]

SKILL_KEYS = [
    "skills",
    "skill",
    "skill_set",
    "key_skills",
    "keyskills",
    "skills_required",
    "job_skills",
]

ROLE_KEYS = [
    "role",
    "job_title",
    "title",
    "designation",
    "category",
]

SPLIT_RE = re.compile(r"[|,;/]\s*")


def _normalize_role(value):
    if not value:
        return None
    text = str(value).strip().lower()
    if text in ROLE_ALIASES:
        return ROLE_ALIASES[text]
    for alias, role in ROLE_ALIASES.items():
        if alias in text:
            return role
    return None


def _parse_skills(value):
    if not value:
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = SPLIT_RE.split(str(value))
    skills = [s.strip().lower() for s in raw if s and str(s).strip()]
    return list(dict.fromkeys(skills))


def _extract_from_row(row):
    headers = {k.lower(): k for k in row.keys() if k}

    text = None
    for key in TEXT_KEYS:
        if key in headers:
            text = row.get(headers[key])
            break

    skills = []
    for key in SKILL_KEYS:
        if key in headers:
            skills = _parse_skills(row.get(headers[key]))
            break

    role = None
    for key in ROLE_KEYS:
        if key in headers:
            role = _normalize_role(row.get(headers[key]))
            if role:
                break

    return text, skills, role


def _insert_batches(collection, batch):
    if not batch:
        return 0
    db = get_db()
    result = db[collection].insert_many(batch)
    return len(result.inserted_ids)


def _handle_csv(path, source_name):
    skill_batch = []
    role_batch = []
    inserted = {"skill": 0, "role": 0}
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text, skills, role = _extract_from_row(row)
            if text and skills:
                skill_batch.append({
                    "text": str(text),
                    "skills": skills,
                    "source": source_name,
                    "created_at": datetime.utcnow(),
                })
            if skills and role:
                role_batch.append({
                    "skills": skills,
                    "role": role,
                    "source": source_name,
                    "created_at": datetime.utcnow(),
                })
            if len(skill_batch) >= 1000:
                inserted["skill"] += _insert_batches("skill_training", skill_batch)
                skill_batch = []
            if len(role_batch) >= 1000:
                inserted["role"] += _insert_batches("role_training", role_batch)
                role_batch = []

    inserted["skill"] += _insert_batches("skill_training", skill_batch)
    inserted["role"] += _insert_batches("role_training", role_batch)
    return inserted


def _handle_jsonl(path, source_name):
    skill_batch = []
    role_batch = []
    inserted = {"skill": 0, "role": 0}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            text, skills, role = _extract_from_row(row)
            if text and skills:
                skill_batch.append({
                    "text": str(text),
                    "skills": skills,
                    "source": source_name,
                    "created_at": datetime.utcnow(),
                })
            if skills and role:
                role_batch.append({
                    "skills": skills,
                    "role": role,
                    "source": source_name,
                    "created_at": datetime.utcnow(),
                })
            if len(skill_batch) >= 1000:
                inserted["skill"] += _insert_batches("skill_training", skill_batch)
                skill_batch = []
            if len(role_batch) >= 1000:
                inserted["role"] += _insert_batches("role_training", role_batch)
                role_batch = []

    inserted["skill"] += _insert_batches("skill_training", skill_batch)
    inserted["role"] += _insert_batches("role_training", role_batch)
    return inserted


def _handle_docx(path, source_name):
    document = Document(path)
    text = "\n".join([p.text for p in document.paragraphs])
    if not text.strip():
        return {"skill": 0, "role": 0}
    # Without labeled skills, skip training insert
    db = get_db()
    db["raw_documents"].insert_one({
        "text": text,
        "source": source_name,
        "created_at": datetime.utcnow(),
    })
    return {"skill": 0, "role": 0}


def _handle_zip(path):
    inserted = {"skill": 0, "role": 0}
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            if name.lower().endswith(".csv"):
                with zf.open(name) as fh:
                    reader = csv.DictReader((line.decode("utf-8", errors="ignore") for line in fh))
                    skill_batch = []
                    role_batch = []
                    for row in reader:
                        text, skills, role = _extract_from_row(row)
                        if text and skills:
                            skill_batch.append({
                                "text": str(text),
                                "skills": skills,
                                "source": f"{path}:{name}",
                                "created_at": datetime.utcnow(),
                            })
                        if skills and role:
                            role_batch.append({
                                "skills": skills,
                                "role": role,
                                "source": f"{path}:{name}",
                                "created_at": datetime.utcnow(),
                            })
                        if len(skill_batch) >= 1000:
                            inserted["skill"] += _insert_batches("skill_training", skill_batch)
                            skill_batch = []
                        if len(role_batch) >= 1000:
                            inserted["role"] += _insert_batches("role_training", role_batch)
                            role_batch = []

                    inserted["skill"] += _insert_batches("skill_training", skill_batch)
                    inserted["role"] += _insert_batches("role_training", role_batch)
    return inserted


def import_paths(paths):
    totals = {"skill": 0, "role": 0, "skipped": 0}
    for path in paths:
        path = str(path)
        if not os.path.exists(path):
            totals["skipped"] += 1
            continue
        if os.path.isdir(path):
            for root, _dirs, files in os.walk(path):
                for name in files:
                    totals = _merge_totals(totals, import_paths([os.path.join(root, name)]))
            continue
        lower = path.lower()
        source_name = Path(path).name
        if lower.endswith(".csv"):
            inserted = _handle_csv(path, source_name)
        elif lower.endswith(".jsonl"):
            inserted = _handle_jsonl(path, source_name)
        elif lower.endswith(".docx"):
            inserted = _handle_docx(path, source_name)
        elif lower.endswith(".zip"):
            inserted = _handle_zip(path)
        else:
            totals["skipped"] += 1
            continue
        totals["skill"] += inserted["skill"]
        totals["role"] += inserted["role"]
    return totals


def _merge_totals(base, extra):
    return {
        "skill": base["skill"] + extra.get("skill", 0),
        "role": base["role"] + extra.get("role", 0),
        "skipped": base["skipped"] + extra.get("skipped", 0),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python import_mongo_datasets.py <path1> <path2> ...")
        raise SystemExit(1)

    summary = import_paths(sys.argv[1:])
    print(f"Imported skill training docs: {summary['skill']}")
    print(f"Imported role training docs: {summary['role']}")
    print(f"Skipped paths: {summary['skipped']}")
