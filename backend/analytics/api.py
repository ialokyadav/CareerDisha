from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analytics.performance_tracker import get_user_history, get_skill_accuracy_summary
from common.mongodb import get_db


class PerformanceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = get_user_history(request.user.id)
        for doc in history:
            doc["_id"] = str(doc["_id"])
        return Response({"history": history})


class SkillAccuracySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accuracy = get_skill_accuracy_summary(request.user.id)
        return Response({"skill_accuracy": accuracy})


class DashboardSnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            db = get_db()
            user_id = request.user.id

            user_doc = db["users"].find_one({"user_id": user_id}) or {}
            target_role = user_doc.get("last_target_role")
            if not target_role:
                latest_roadmap = db["roadmaps"].find_one({"user_id": user_id}, sort=[("created_at", -1)])
                target_role = latest_roadmap.get("target_role") if latest_roadmap else None

            extraction_doc = db["skill_extractions"].find_one({"user_id": user_id}, sort=[("created_at", -1)])
            raw_skills = extraction_doc.get("skills", []) if extraction_doc else []
            resume_skills = []
            for skill_item in raw_skills:
                if isinstance(skill_item, dict):
                    val = str(skill_item.get("skill", "")).strip().lower()
                else:
                    val = str(skill_item).strip().lower()
                if val:
                    resume_skills.append(val)

            learned = []
            learning = []
            still_missing = []

            roadmap_doc = None
            progress_doc = None
            if target_role:
                roadmap_doc = db["roadmaps"].find_one(
                    {"user_id": user_id, "target_role": target_role},
                    sort=[("created_at", -1)],
                )
                progress_doc = db["roadmap_progress"].find_one(
                    {"user_id": user_id, "target_role": target_role}
                )

            if roadmap_doc and progress_doc:
                status_by_phase = {p.get("phase"): p.get("status") for p in progress_doc.get("phases", []) if isinstance(p, dict)}
                roadmap_data = roadmap_doc.get("roadmap", {})
                phase_items = roadmap_data.get("roadmap", []) if isinstance(roadmap_data, dict) else []
                for phase in phase_items:
                    if not isinstance(phase, dict):
                        continue
                    phase_name = phase.get("phase")
                    phase_status = status_by_phase.get(phase_name)
                    phase_skills = []
                    for s in phase.get("skills", []):
                        if isinstance(s, dict):
                            name = str(s.get("name", "")).strip().lower()
                        else:
                            name = str(s).strip().lower()
                        if name:
                            phase_skills.append(name)
                    if phase_status == "Completed":
                        learned.extend(phase_skills)
                    elif phase_status == "Unlocked":
                        learning.extend(phase_skills)
                    else:
                        still_missing.extend(phase_skills)

            gap_doc = None
            if target_role:
                gap_doc = db["skill_gaps"].find_one(
                    {"user_id": user_id, "target_role": target_role},
                    sort=[("created_at", -1)],
                )
            if not gap_doc:
                gap_doc = db["skill_gaps"].find_one({"user_id": user_id}, sort=[("created_at", -1)])

            gap_missing = []
            if gap_doc:
                gap_data = gap_doc.get("gap", {})
                if isinstance(gap_data, dict):
                    raw_missing = gap_data.get("missing_skills", [])
                    if isinstance(raw_missing, list):
                        gap_missing = [str(s).strip().lower() for s in raw_missing if str(s).strip()]

            learned_set = set(learned)
            learning_set = set(learning)
            still_missing_set = set(still_missing) | set(gap_missing)
            still_missing_set -= learned_set
            still_missing_set -= learning_set

            return Response(
                {
                    "username": request.user.username,
                    "target_role": target_role,
                    "skills": {
                        "resume": sorted(set(resume_skills)),
                        "learned_missing": sorted(learned_set),
                        "learning_missing": sorted(learning_set),
                        "still_missing": sorted(still_missing_set),
                    },
                }
            )
        except Exception as exc:
            return Response(
                {
                    "username": request.user.username,
                    "target_role": None,
                    "skills": {
                        "resume": [],
                        "learned_missing": [],
                        "learning_missing": [],
                        "still_missing": [],
                    },
                    "error": f"dashboard_snapshot_failed: {str(exc)}",
                },
                status=200,
            )


urlpatterns = [
    path("", DashboardSnapshotView.as_view(), name="dashboard-snapshot-root"),
    path("history/", PerformanceHistoryView.as_view(), name="performance-history"),
    path("summary/", SkillAccuracySummaryView.as_view(), name="skill-summary"),
    path("dashboard/", DashboardSnapshotView.as_view(), name="dashboard-snapshot"),
    path("dashboard-snapshot/", DashboardSnapshotView.as_view(), name="dashboard-snapshot-legacy"),
]
