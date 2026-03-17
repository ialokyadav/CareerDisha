from collections import defaultdict
from datetime import datetime
from roadmap.role_skill_map import ROLE_SKILL_MAP, SKILL_METADATA, DEFAULT_SKILL_TEMPLATE
from ml_engine.skill_gap_analyzer import get_required_skills

PHASE_ORDER = ["Foundation", "Core", "Advanced"]
STATUS_MISSING = "Missing"
STATUS_WEAK = "Weak"
STATUS_MATCHED = "Matched"
ROLE_ALIASES = {
    "cloud architect": "Cloud Engineer",
    "cybersecurity expert": "Cyber Security Analyst",
    "cyber security expert": "Cyber Security Analyst",
}


def _normalize_skill(skill):
    return skill.strip().lower()


def _normalize_role(role):
    if not isinstance(role, str):
        return ""
    text = role.strip()
    if not text:
        return ""
    alias = ROLE_ALIASES.get(text.lower())
    return alias or text


def _get_skill_meta(skill):
    meta = SKILL_METADATA.get(skill, DEFAULT_SKILL_TEMPLATE)
    return {
        "level": meta.get("level", "Core"),
        "topics": meta.get("topics", DEFAULT_SKILL_TEMPLATE["topics"]),
        "prerequisites": meta.get("prerequisites", []),
        "eta_weeks": meta.get("eta_weeks", 2),
        "assessment_type": meta.get("assessment_type", ["MCQ"]),
    }


def _adjust_for_performance(skill, meta, performance_history):
    accuracy = performance_history.get(skill)
    eta = meta["eta_weeks"]
    assessment_type = list(meta["assessment_type"])

    if accuracy is None:
        return eta, assessment_type
    if accuracy > 1:
        accuracy = accuracy / 100.0

    if accuracy < 0.6:
        eta = eta + 1
        if "MCQ" not in assessment_type:
            assessment_type.append("MCQ")
    elif accuracy >= 0.85:
        eta = max(1, eta - 1)
    return eta, assessment_type


def _ensure_prerequisites(skills, performance_history, missing_set, weak_set):
    expanded = set(skills)
    queue = list(skills)
    while queue:
        skill = queue.pop()
        meta = _get_skill_meta(skill)
        for prereq in meta["prerequisites"]:
            prereq = _normalize_skill(prereq)
            if prereq not in expanded:
                expanded.add(prereq)
                queue.append(prereq)
                if prereq not in missing_set and prereq not in weak_set:
                    # If not listed, treat as missing prerequisite
                    missing_set.add(prereq)
    return expanded


def generate_role_roadmap(payload):
    """
    Generate a role-specific learning roadmap based on user skills and progress.
    Follows strict JSON format specified by user.
    """
    requested_target_role = payload.get("target_role")
    if isinstance(requested_target_role, str) and requested_target_role.strip():
        target_role = _normalize_role(requested_target_role)
    else:
        target_role = "Machine Learning Engineer"
    user_skills = {s.lower() for s in payload.get("user_skills", [])}
    progress_updates = payload.get("progress_updates", {})
    completed_updates = {s.lower() for s in progress_updates.get("completed", [])}
    in_progress_updates = {s.lower() for s in progress_updates.get("in_progress", [])}
    completed_score_updates = {}
    for k, v in (progress_updates.get("completed_scores", {}) or {}).items():
        key = str(k).strip().lower()
        if not key:
            continue
        try:
            completed_score_updates[key] = float(v)
        except (TypeError, ValueError):
            continue

    in_progress_score_updates = {}
    for k, v in (progress_updates.get("in_progress_scores", {}) or {}).items():
        key = str(k).strip().lower()
        if not key:
            continue
        try:
            in_progress_score_updates[key] = float(v)
        except (TypeError, ValueError):
            continue

    role_skills = ROLE_SKILL_MAP.get(target_role)
    if not role_skills:
        # Try dynamic role skills from training data when role is not in static roadmap map.
        try:
            dynamic_skills = get_required_skills(target_role)
            role_skills = [s.strip().lower() for s in dynamic_skills if str(s).strip()]
        except Exception:
            role_skills = None
    if not role_skills:
        role_skills = ROLE_SKILL_MAP.get("Software Developer")
        target_role = "Software Developer"

    phase_map = defaultdict(lambda: {"skills": [], "description": ""})
    
    # Pre-populate phase descriptions (could be moved to role_skill_map metadata)
    phase_meta = {
        "Foundation": "Core programming and math skills",
        "Core": "Essential domain-specific skills and frameworks",
        "Advanced": "Specialized topics and production practices"
    }

    all_roadmap_skills = []

    for skill_name in role_skills:
        skill_lower = skill_name.lower()
        meta = SKILL_METADATA.get(skill_lower, DEFAULT_SKILL_TEMPLATE)
        phase = meta.get("level", "Core")
        
        # Determine status
        if skill_lower in completed_updates or skill_lower in user_skills:
            status = "completed"
        elif skill_lower in in_progress_updates:
            status = "in_progress"
        else:
            status = "pending"
        
        skill_entry = {
            "name": skill_name.title() if skill_name.islower() else skill_name,
            "status": status
        }
        if status == "completed" and skill_lower in completed_score_updates:
            skill_entry["score"] = completed_score_updates[skill_lower]
        if status == "in_progress" and skill_lower in in_progress_score_updates:
            skill_entry["score"] = in_progress_score_updates[skill_lower]
        
        if phase not in phase_map:
            phase_map[phase] = {"phase": phase, "description": phase_meta.get(phase, ""), "skills": []}
        
        phase_map[phase]["skills"].append(skill_entry)
        all_roadmap_skills.append(skill_entry)

    # Sort roadmap by PHASE_ORDER
    ordered_roadmap = []
    for p_name in PHASE_ORDER:
        if p_name in phase_map:
            ordered_roadmap.append(phase_map[p_name])

    # Summary calculations
    completed_count = sum(1 for s in all_roadmap_skills if s["status"] == "completed")
    in_progress_count = sum(1 for s in all_roadmap_skills if s["status"] == "in_progress")
    pending_count = sum(1 for s in all_roadmap_skills if s["status"] == "pending")
    total_count = len(all_roadmap_skills)
    completion_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0

    # Next recommended skills (first 3 pending skills in phase order)
    next_recommended = [s["name"] for s in all_roadmap_skills if s["status"] == "pending"][:3]

    matched_skills = sorted([s["name"] for s in all_roadmap_skills if s["status"] == "completed"])
    in_progress_skills = sorted([s["name"] for s in all_roadmap_skills if s["status"] == "in_progress"])
    missing_skills = sorted([s["name"] for s in all_roadmap_skills if s["status"] == "pending"])
    completed_skill_scores = {
        s["name"]: s["score"]
        for s in all_roadmap_skills
        if s["status"] == "completed" and "score" in s
    }
    in_progress_skill_scores = {
        s["name"]: s["score"]
        for s in all_roadmap_skills
        if s["status"] == "in_progress" and "score" in s
    }

    return {
        "target_role": target_role,
        "roadmap": ordered_roadmap,
        "summary": {
            "completed_skills_count": completed_count,
            "in_progress_skills_count": in_progress_count,
            "pending_skills_count": pending_count,
            "completion_percentage": completion_percentage
        },
        "skills_snapshot": {
            "matched_skills": matched_skills,
            "in_progress_skills": in_progress_skills,
            "missing_skills": missing_skills,
            "completed_skill_scores": completed_skill_scores,
            "in_progress_skill_scores": in_progress_skill_scores,
        },
        "next_recommended_skills": next_recommended
    }
