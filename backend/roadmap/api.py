from datetime import datetime
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from common.mongodb import get_db
from analytics.performance_tracker import get_skill_accuracy_summary
from roadmap.roadmap_engine import generate_role_roadmap


class GenerateRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        target_role = request.data.get("target_role")
        requested_user_id = request.data.get("user_id")

        if not target_role:
            return Response({"error": "target_role required"}, status=status.HTTP_400_BAD_REQUEST)

        if requested_user_id and request.user.is_staff:
            user_id = int(requested_user_id)
        else:
            user_id = request.user.id

        db = get_db()
        gap_doc = db["skill_gaps"].find_one(
            {"user_id": user_id, "target_role": target_role},
            sort=[("created_at", -1)],
        )

        if not gap_doc:
            return Response({"error": "skill gap not found for target_role"}, status=status.HTTP_404_NOT_FOUND)

        gap = gap_doc.get("gap", {})
        # Get user skills from last extraction
        skill_doc = db["skill_extractions"].find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        user_skills = [s["skill"] for s in skill_doc["skills"]] if skill_doc else []

        # Get progress updates from roadmap_progress
        progress_doc = db["roadmap_progress"].find_one(
            {"user_id": user_id, "target_role": target_role}
        )
        
        # In this simplified implementation, we map completed phases to completed skills
        # or we might have a specific 'completed_skills' list in progress_doc
        completed_skills = []
        in_progress_skills = []
        if progress_doc:
            for phase in progress_doc.get("phases", []):
                if phase.get("status") == "Completed":
                    # For simplicity, if phase is completed, we mark its skills as completed
                    # In a real app, this would be more granular
                    pass 
            # We can also check a hypothetical 'manual_progress' field
            completed_skills = progress_doc.get("completed_skills", [])
            in_progress_skills = progress_doc.get("in_progress_skills", [])

        payload = {
            "user_id": str(user_id),
            "target_role": target_role,
            "user_skills": user_skills,
            "progress_updates": {
                "completed": completed_skills,
                "in_progress": in_progress_skills
            }
        }

        try:
            roadmap = generate_role_roadmap(payload)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        store_doc = {
            "user_id": user_id,
            "target_role": target_role,
            "roadmap": roadmap,
            "created_at": datetime.utcnow(),
        }
        inserted = db["roadmaps"].insert_one(store_doc)

        response = roadmap
        response["roadmap_id"] = str(inserted.inserted_id)
        return Response(response)


urlpatterns = [
    path("generate/", GenerateRoadmapView.as_view(), name="generate-roadmap"),
]
