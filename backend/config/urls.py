from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import RegisterView, ProfileView

def health_view(_request):
    return JsonResponse({"status": "ok", "service": "skill-assessment-backend"})


def favicon_view(_request):
    # Prevent 404 noise in dev; browsers often request /favicon.ico
    return JsonResponse({}, status=204)

urlpatterns = [
    path("", health_view, name="health"),
    path("favicon.ico", favicon_view, name="favicon"),
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/profile/", ProfileView.as_view(), name="profile"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/resumes/", include("resumes.api")),
    path("api/assessments/", include("assessments.api")),
    path("api/analytics/", include("analytics.api")),
    path("api/roadmap/", include("roadmap.api")),
]
