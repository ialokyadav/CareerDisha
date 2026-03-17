from datetime import datetime
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from common.mongodb import get_db
from roadmap.roadmap_engine import generate_role_roadmap
from roadmap.progress_utils import init_progress, get_progress
from ml_engine.role_predictor import predict_role


class GenerateRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        requested_target_role = request.data.get("target_role")
        requested_user_id = request.data.get("user_id")
        role_source = "target"

        if requested_user_id and request.user.is_staff:
            user_id = int(requested_user_id)
        else:
            user_id = request.user.id

        db = get_db()

        # Get user skills: prefer request data, fallback to last extraction
        request_skills = request.data.get("user_skills")
        if request_skills and isinstance(request_skills, list):
            user_skills = request_skills
        else:
            skill_doc = db["skill_extractions"].find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            user_skills = [s["skill"] for s in skill_doc["skills"]] if skill_doc else []

        # If target role is not explicitly set, infer from user skills when available.
        if not requested_target_role:
            role_source = "predicted"
            if user_skills:
                try:
                    predicted_role, _confidence = predict_role(user_skills)
                    requested_target_role = predicted_role
                except Exception:
                    requested_target_role = None

        # Get progress updates from roadmap_progress
        progress_doc = None
        if requested_target_role:
            progress_doc = db["roadmap_progress"].find_one(
                {"user_id": user_id, "target_role": requested_target_role}
            )
        
        # In this simplified implementation, we map completed phases to completed skills
        # or we might have a specific 'completed_skills' list in progress_doc
        completed_skills = []
        in_progress_skills = []
        completed_skill_scores = {}
        in_progress_skill_scores = {}
        if progress_doc:
            for phase in progress_doc.get("phases", []):
                if phase.get("status") == "Completed":
                    # For simplicity, if phase is completed, we mark its skills as completed
                    # In a real app, this would be more granular
                    pass 
            # We can also check a hypothetical 'manual_progress' field
            completed_skills = progress_doc.get("completed_skills", [])
            in_progress_skills = progress_doc.get("in_progress_skills", [])
            completed_skill_scores = progress_doc.get("completed_skill_scores", {}) or {}
            in_progress_skill_scores = progress_doc.get("in_progress_skill_scores", {}) or {}

        payload = {
            "user_id": str(user_id),
            "user_skills": user_skills,
            "progress_updates": {
                "completed": completed_skills,
                "in_progress": in_progress_skills,
                "completed_scores": completed_skill_scores,
                "in_progress_scores": in_progress_skill_scores,
            }
        }
        if requested_target_role:
            payload["target_role"] = requested_target_role

        try:
            roadmap = generate_role_roadmap(payload)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        resolved_target_role = roadmap.get("target_role")
        db["users"].update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "last_target_role": resolved_target_role,
                    "last_target_role_updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )

        store_doc = {
            "user_id": user_id,
            "target_role": resolved_target_role,
            "roadmap": roadmap,
            "created_at": datetime.utcnow(),
        }
        inserted = db["roadmaps"].insert_one(store_doc)
        progress = init_progress(
            db=db,
            user_id=user_id,
            target_role=resolved_target_role,
            roadmap_id=inserted.inserted_id,
            roadmap=roadmap.get("roadmap", []),
        )

        response = roadmap
        response["roadmap_id"] = str(inserted.inserted_id)
        response["progress"] = _serialize_progress(progress)
        response["role_source"] = role_source
        return Response(response)


class RoadmapProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_role = request.query_params.get("target_role")
        if not target_role:
            return Response({"error": "target_role required"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        progress = get_progress(db, request.user.id, target_role)

        if not progress:
            roadmap_doc = db["roadmaps"].find_one(
                {"user_id": request.user.id, "target_role": target_role},
                sort=[("created_at", -1)],
            )
            if not roadmap_doc:
                return Response({"error": "roadmap not found for target_role"}, status=status.HTTP_404_NOT_FOUND)
            progress = init_progress(
                db=db,
                user_id=request.user.id,
                target_role=target_role,
                roadmap_id=roadmap_doc.get("_id"),
                roadmap=roadmap_doc.get("roadmap", {}).get("roadmap", []),
            )

        return Response({"target_role": target_role, "progress": _serialize_progress(progress)})


def _serialize_progress(progress_doc):
    phases = []
    for phase in progress_doc.get("phases", []):
        completed_at = phase.get("completed_at")
        phases.append(
            {
                "phase": phase.get("phase"),
                "status": phase.get("status"),
                "last_test_id": phase.get("last_test_id"),
                "last_score": phase.get("last_score"),
                "completed_at": completed_at.isoformat() if completed_at else None,
            }
        )
    return {
        "active_phase": progress_doc.get("active_phase"),
        "phases": phases,
        "updated_at": progress_doc.get("updated_at").isoformat() if progress_doc.get("updated_at") else None,
    }


urlpatterns = [
    path("generate/", GenerateRoadmapView.as_view(), name="generate-roadmap"),
    path("progress/", RoadmapProgressView.as_view(), name="roadmap-progress"),
]
