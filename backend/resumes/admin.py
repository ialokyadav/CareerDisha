from django.contrib import admin
from .models import MongoResume, MongoExtraction, MongoPrediction
from common.mongodb import get_db
from django.utils.html import format_html

class MongoDBAdmin(admin.ModelAdmin):
    """Base Admin for MongoDB collections"""
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        db = get_db()
        # Fetch data directly from Mongo for the list view
        collection_name = self.collection_name
        data = list(db[collection_name].find().sort("created_at", -1).limit(50))
        
        # Convert ObjectId and format for template
        for item in data:
            item['id'] = str(item.get('_id'))
            if 'user_id' in item:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=item['user_id'])
                    item['user_display'] = f"{user.username} (ID: {user.id})"
                except User.DoesNotExist:
                    item['user_display'] = f"Unknown User ({item['user_id']})"
        
        extra_context['mongo_data'] = data
        extra_context['mongo_fields'] = self.mongo_fields
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(MongoResume)
class MongoResumeAdmin(MongoDBAdmin):
    collection_name = "resumes"
    mongo_fields = ["id", "user_display", "filename", "extension", "created_at"]
    change_list_template = "admin/mongo_changelist.html"

@admin.register(MongoExtraction)
class MongoExtractionAdmin(MongoDBAdmin):
    collection_name = "skill_extractions"
    mongo_fields = ["id", "user_display", "skills_short", "created_at"]
    change_list_template = "admin/mongo_changelist.html"

    def skills_short(self, item):
        skills = [s.get("skill") for s in item.get("skills", [])[:5]]
        return ", ".join(skills) + ("..." if len(item.get("skills", [])) > 5 else "")

@admin.register(MongoPrediction)
class MongoPredictionAdmin(MongoDBAdmin):
    collection_name = "role_predictions"
    mongo_fields = ["id", "user_display", "predicted_role", "confidence_fmt", "created_at"]
    change_list_template = "admin/mongo_changelist.html"

    def confidence_fmt(self, item):
        return f"{item.get('confidence', 0)*100:.1f}%"
