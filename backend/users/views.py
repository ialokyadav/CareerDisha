from rest_framework import generics, permissions
from common.mongodb import get_db
from datetime import datetime
from django.contrib.auth.models import User
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
