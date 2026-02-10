from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analytics.performance_tracker import get_user_history, get_skill_accuracy_summary


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


urlpatterns = [
    path("history/", PerformanceHistoryView.as_view(), name="performance-history"),
    path("summary/", SkillAccuracySummaryView.as_view(), name="skill-summary"),
]
