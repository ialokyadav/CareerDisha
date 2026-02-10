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
