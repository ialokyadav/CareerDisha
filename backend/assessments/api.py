from datetime import datetime
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from common.mongodb import get_db
from assessments.question_bank import seed_questions, list_questions
from assessments.test_generator import build_skill_priority, generate_test
from assessments.evaluation import evaluate_attempt
from ml_engine.skill_gap_analyzer import analyze_skill_gap
from ml_engine.adaptive_engine import adjust_difficulty
from ml_engine.role_predictor import ALLOWED_ROLES
from analytics.performance_tracker import record_attempt, get_skill_accuracy_summary


class SeedQuestionBankView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        questions = request.data.get("questions", [])
        normalized = []
        for q in questions:
            required = {"question", "options", "correct_answer", "skill", "difficulty"}
            if not required.issubset(set(q.keys())):
                return Response({"error": "invalid question schema"}, status=status.HTTP_400_BAD_REQUEST)
            if q["difficulty"] not in ["Easy", "Medium", "Hard"]:
                return Response({"error": "invalid difficulty"}, status=status.HTTP_400_BAD_REQUEST)
            normalized.append(q)

        inserted = seed_questions(normalized)
        return Response({"inserted": inserted})


class ListQuestionBankView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        skill = request.query_params.get("skill")
        difficulty = request.query_params.get("difficulty")
        questions = list_questions(skill=skill, difficulty=difficulty)
        for q in questions:
            q["_id"] = str(q["_id"])
        return Response({"questions": questions})


class GenerateTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        target_role = request.data.get("target_role")
        skills = request.data.get("skills", [])
        missing_skills = request.data.get("missing_skills", [])
        weak_skills = request.data.get("weak_skills", [])
        total_questions = int(request.data.get("total_questions", 10))
        base_difficulty = request.data.get("difficulty", "Medium")

        if not target_role:
            return Response({"error": "target_role required"}, status=status.HTTP_400_BAD_REQUEST)

        if not missing_skills or not weak_skills:
            if not skills:
                return Response({"error": "skills required to derive skill gap"}, status=status.HTTP_400_BAD_REQUEST)
            performance = get_skill_accuracy_summary(request.user.id)
            gap = analyze_skill_gap(skills, target_role, performance=performance)
            missing_skills = gap["missing_skills"]
            weak_skills = gap["weak_skills"]
            required_skills = gap["required_skills"]
        else:
            required_skills = []

        skills_priority = build_skill_priority(missing_skills, weak_skills, required_skills)
        questions = generate_test(skills_priority, base_difficulty=base_difficulty, total_questions=total_questions)

        if not questions:
            return Response({"error": "no questions available"}, status=status.HTTP_404_NOT_FOUND)

        db = get_db()
        test_doc = {
            "user_id": request.user.id,
            "target_role": target_role,
            "skills_priority": skills_priority,
            "difficulty": base_difficulty,
            "questions": [str(q["_id"]) for q in questions],
            "created_at": datetime.utcnow(),
        }
        test_id = db["tests"].insert_one(test_doc).inserted_id

        for q in questions:
            q["_id"] = str(q["_id"])
            q.pop("correct_answer", None)

        return Response({"test_id": str(test_id), "questions": questions})


class SubmitTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        test_id = request.data.get("test_id")
        answers = request.data.get("answers", {})
        if not test_id:
            return Response({"error": "test_id required"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        # Fetch by string id
        try:
            from bson import ObjectId
            test_doc = db["tests"].find_one({"_id": ObjectId(test_id)})
        except Exception:
            test_doc = None

        if not test_doc:
            return Response({"error": "test not found"}, status=status.HTTP_404_NOT_FOUND)

        question_ids = test_doc.get("questions", [])
        object_ids = [oid for oid in (__to_object_id(qid) for qid in question_ids) if oid]
        questions = list(db["question_bank"].find({"_id": {"$in": object_ids}}))

        result = evaluate_attempt(questions, answers)
        next_difficulty = adjust_difficulty(result["accuracy"], test_doc.get("difficulty", "Medium"))

        attempt_doc = record_attempt(request.user.id, test_doc.get("target_role"), result, test_doc.get("difficulty"))

        db["tests"].update_one({"_id": test_doc["_id"]}, {"$set": {"last_result": result, "next_difficulty": next_difficulty}})

        attempt_doc["_id"] = str(attempt_doc.get("_id", ""))
        return Response({
            "result": {
                "accuracy": result["accuracy"],
                "total": result["total"],
                "correct": result["correct"],
                "skill_stats": result["skill_stats"],
                "next_difficulty": next_difficulty,
            }
        })


class ListRolesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"roles": ALLOWED_ROLES})


def __to_object_id(value):
    from bson import ObjectId
    try:
        return ObjectId(value)
    except Exception:
        return None


urlpatterns = [
    path("questions/seed/", SeedQuestionBankView.as_view(), name="seed-questions"),
    path("questions/", ListQuestionBankView.as_view(), name="list-questions"),
    path("roles/", ListRolesView.as_view(), name="list-roles"),
    path("generate/", GenerateTestView.as_view(), name="generate-test"),
    path("submit/", SubmitTestView.as_view(), name="submit-test"),
]
