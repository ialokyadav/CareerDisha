import hashlib
import random
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.mongodb import get_db
from .serializers import RegisterSerializer, ProfileSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        db = get_db()
        db["users"].insert_one(
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": "Admin" if user.is_staff else "Student",
                "created_at": datetime.utcnow(),
            }
        )


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        user = self.request.user
        # Ensure MongoDB user document exists/updated
        db = get_db()
        db["users"].update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": "Admin" if user.is_staff else "Student",
                    "last_seen": datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )
        return user


class RequestPasswordResetOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        email = str(request.data.get("email", "")).strip().lower()

        if not username or not email:
            return Response({"error": "username and email are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "invalid username or email"}, status=status.HTTP_400_BAD_REQUEST)

        if (user.email or "").strip().lower() != email:
            return Response({"error": "invalid username or email"}, status=status.HTTP_400_BAD_REQUEST)

        otp = f"{random.randint(0, 999999):06d}"
        otp_hash = hashlib.sha256(otp.encode("utf-8")).hexdigest()
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=10)

        db = get_db()
        db["password_reset_otps"].update_many(
            {"user_id": user.id, "used": {"$ne": True}},
            {"$set": {"used": True, "invalidated_at": now}},
        )
        db["password_reset_otps"].insert_one(
            {
                "user_id": user.id,
                "username": user.username,
                "email": email,
                "otp_hash": otp_hash,
                "attempts": 0,
                "max_attempts": 5,
                "created_at": now,
                "expires_at": expires_at,
                "used": False,
            }
        )

        try:
            send_mail(
                subject="CareerDisha AI Password Reset OTP",
                message=f"Your OTP is {otp}. It will expire in 10 minutes.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@careerdisha.ai"),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            return Response({"error": "failed to send OTP email. please try again later"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)


class VerifyPasswordResetOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        email = str(request.data.get("email", "")).strip().lower()
        otp = str(request.data.get("otp", "")).strip()
        new_password = str(request.data.get("new_password", ""))
        confirm_password = str(request.data.get("confirm_password", ""))

        if not username or not email or not otp or not new_password or not confirm_password:
            return Response({"error": "username, email, otp, new_password and confirm_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"error": "password must be at least 8 characters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "invalid username or email"}, status=status.HTTP_400_BAD_REQUEST)

        if (user.email or "").strip().lower() != email:
            return Response({"error": "invalid username or email"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        otp_doc = db["password_reset_otps"].find_one(
            {"user_id": user.id, "email": email, "used": {"$ne": True}},
            sort=[("created_at", -1)],
        )
        if not otp_doc:
            return Response({"error": "no active OTP request found"}, status=status.HTTP_400_BAD_REQUEST)

        now = datetime.utcnow()
        if otp_doc.get("expires_at") and otp_doc["expires_at"] < now:
            db["password_reset_otps"].update_one(
                {"_id": otp_doc["_id"]},
                {"$set": {"used": True, "expired_at": now}},
            )
            return Response({"error": "OTP expired. request a new OTP"}, status=status.HTTP_400_BAD_REQUEST)

        attempts = int(otp_doc.get("attempts", 0))
        max_attempts = int(otp_doc.get("max_attempts", 5))
        if attempts >= max_attempts:
            db["password_reset_otps"].update_one(
                {"_id": otp_doc["_id"]},
                {"$set": {"used": True, "locked_at": now}},
            )
            return Response({"error": "maximum OTP attempts exceeded. request a new OTP"}, status=status.HTTP_400_BAD_REQUEST)

        otp_hash = hashlib.sha256(otp.encode("utf-8")).hexdigest()
        if otp_hash != otp_doc.get("otp_hash"):
            new_attempts = attempts + 1
            update_doc = {"attempts": new_attempts}
            if new_attempts >= max_attempts:
                update_doc["used"] = True
                update_doc["locked_at"] = now
            db["password_reset_otps"].update_one(
                {"_id": otp_doc["_id"]},
                {"$set": update_doc},
            )
            return Response({"error": "invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        db["password_reset_otps"].update_one(
            {"_id": otp_doc["_id"]},
            {"$set": {"used": True, "verified": True, "used_at": now}},
        )

        return Response({"message": "password updated successfully"}, status=status.HTTP_200_OK)
