from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from common.mongodb import get_db

# Unregister the default User model
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ("mongo_role", "mongo_last_seen", "mongo_data_link")

    def mongo_role(self, obj):
        db = get_db()
        doc = db["users"].find_one({"user_id": obj.id})
        return doc.get("role", "N/A") if doc else "No Mongo Profile"
    mongo_role.short_description = "Role (Mongo)"

    def mongo_last_seen(self, obj):
        db = get_db()
        doc = db["users"].find_one({"user_id": obj.id})
        if doc and "last_seen" in doc:
            return doc["last_seen"].strftime("%Y-%m-%d %H:%M")
        return "Never"
    mongo_last_seen.short_description = "Last Seen (Mongo)"

    def mongo_data_link(self, obj):
        # Placeholder for future deep-link to detailed mongo view
        return format_html('<span style="color: var(--primary);">Synced</span>')
    mongo_data_link.short_description = "Status"
