from datetime import datetime

PHASE_STATUS_LOCKED = "Locked"
PHASE_STATUS_UNLOCKED = "Unlocked"
PHASE_STATUS_COMPLETED = "Completed"


def init_progress(db, user_id, target_role, roadmap_id, roadmap, reset=False):
    existing = db["roadmap_progress"].find_one(
        {"user_id": user_id, "target_role": target_role}
    )
    if existing and not reset:
        return existing

    phases = []
    for idx, phase in enumerate(roadmap):
        status = PHASE_STATUS_UNLOCKED if idx == 0 else PHASE_STATUS_LOCKED
        phases.append({
            "phase": phase.get("phase"),
            "status": status,
            "last_test_id": None,
            "last_score": None,
            "completed_at": None,
        })

    doc = {
        "user_id": user_id,
        "target_role": target_role,
        "roadmap_id": str(roadmap_id),
        "phases": phases,
        "active_phase": phases[0]["phase"] if phases else None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    db["roadmap_progress"].update_one(
        {"user_id": user_id, "target_role": target_role},
        {"$set": doc},
        upsert=True,
    )
    return doc


def get_progress(db, user_id, target_role):
    return db["roadmap_progress"].find_one(
        {"user_id": user_id, "target_role": target_role}
    )


def apply_phase_result(db, progress_doc, phase_name, passed, test_id=None, accuracy=None):
    phases = progress_doc.get("phases", [])
    updated = False
    active_phase = progress_doc.get("active_phase")

    for idx, phase in enumerate(phases):
        if phase.get("phase") != phase_name:
            continue

        if test_id is not None:
            phase["last_test_id"] = str(test_id)
        if accuracy is not None:
            phase["last_score"] = float(accuracy)

        if passed:
            phase["status"] = PHASE_STATUS_COMPLETED
            phase["completed_at"] = datetime.utcnow()
            if idx + 1 < len(phases):
                next_phase = phases[idx + 1]
                if next_phase.get("status") == PHASE_STATUS_LOCKED:
                    next_phase["status"] = PHASE_STATUS_UNLOCKED
                    active_phase = next_phase.get("phase")
            else:
                active_phase = None
        else:
            if phase.get("status") == PHASE_STATUS_LOCKED:
                phase["status"] = PHASE_STATUS_UNLOCKED
            active_phase = phase.get("phase")

        updated = True
        break

    if updated:
        db["roadmap_progress"].update_one(
            {"_id": progress_doc["_id"]},
            {"$set": {"phases": phases, "active_phase": active_phase, "updated_at": datetime.utcnow()}},
        )

    return progress_doc


def _normalize_skill(skill):
    return str(skill).strip().lower()


def apply_skill_results(db, progress_doc, skill_stats, pass_threshold=0.75):
    """
    Update granular skill progress using per-skill test stats.
    - Skill accuracy >= pass_threshold => completed
    - Skill accuracy < pass_threshold  => in_progress (unless already completed)
    """
    if not progress_doc or not isinstance(skill_stats, dict):
        return progress_doc

    completed = {_normalize_skill(s) for s in progress_doc.get("completed_skills", []) if _normalize_skill(s)}
    in_progress = {_normalize_skill(s) for s in progress_doc.get("in_progress_skills", []) if _normalize_skill(s)}
    completed_scores = {
        _normalize_skill(skill): float(score)
        for skill, score in (progress_doc.get("completed_skill_scores", {}) or {}).items()
        if _normalize_skill(skill)
    }
    in_progress_scores = {
        _normalize_skill(skill): float(score)
        for skill, score in (progress_doc.get("in_progress_skill_scores", {}) or {}).items()
        if _normalize_skill(skill)
    }

    changed = False
    for raw_skill, stats in skill_stats.items():
        skill = _normalize_skill(raw_skill)
        if not skill:
            continue

        total = int((stats or {}).get("total", 0))
        correct = int((stats or {}).get("correct", 0))
        if total <= 0:
            continue

        accuracy = correct / total
        score_percent = round(accuracy * 100, 1)
        if accuracy >= float(pass_threshold):
            if skill not in completed:
                completed.add(skill)
                changed = True
            if completed_scores.get(skill) != score_percent:
                completed_scores[skill] = score_percent
                changed = True
            if skill in in_progress:
                in_progress.remove(skill)
                changed = True
            if skill in in_progress_scores:
                in_progress_scores.pop(skill, None)
                changed = True
        else:
            if skill not in completed and skill not in in_progress:
                in_progress.add(skill)
                changed = True
            if skill not in completed and in_progress_scores.get(skill) != score_percent:
                in_progress_scores[skill] = score_percent
                changed = True

    if changed:
        update_fields = {
            "completed_skills": sorted(completed),
            "in_progress_skills": sorted(in_progress),
            "completed_skill_scores": completed_scores,
            "in_progress_skill_scores": in_progress_scores,
            "updated_at": datetime.utcnow(),
        }
        db["roadmap_progress"].update_one({"_id": progress_doc["_id"]}, {"$set": update_fields})
        progress_doc.update(update_fields)

    return progress_doc
