from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=["Student", "Admin"], default="Student")

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", "Student")
        user = User.objects.create_user(**validated_data)
        # Map role to is_staff for Admin
        if role == "Admin":
            user.is_staff = True
            user.is_superuser = False
            user.save(update_fields=["is_staff", "is_superuser"])
        return user


class ProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "is_staff"]

    def get_role(self, obj):
        return "Admin" if obj.is_staff else "Student"
