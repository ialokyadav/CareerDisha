from django.contrib import admin
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import RegisterView, ProfileView, RequestPasswordResetOtpView, VerifyPasswordResetOtpView

def health_view(_request):
    return JsonResponse({"status": "ok", "service": "skill-assessment-backend"})


def favicon_view(_request):
    # Prevent 404 noise in dev; browsers often request /favicon.ico
    return JsonResponse({}, status=204)


def feature_hub_view(request):
    return TemplateResponse(
        request,
        "admin/feature_hub.html",
        {
            "title": "Feature Hub",
            "app_list": admin.site.get_app_list(request),
        },
    )


urlpatterns = [
    path("", health_view, name="health"),
    path("favicon.ico", favicon_view, name="favicon"),
    path("admin/feature-hub/", admin.site.admin_view(feature_hub_view), name="admin-feature-hub"),
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/profile/", ProfileView.as_view(), name="profile"),
    path("api/auth/forgot-password/request-otp/", RequestPasswordResetOtpView.as_view(), name="forgot-password-request-otp"),
    path("api/auth/forgot-password/verify-otp/", VerifyPasswordResetOtpView.as_view(), name="forgot-password-verify-otp"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/resumes/", include("resumes.api")),
    path("api/assessments/", include("assessments.api")),
    path("api/analytics/", include("analytics.api")),
    path("api/roadmap/", include("roadmap.api")),
]
