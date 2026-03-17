from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from common.mongodb import get_db
from resumes.parser import extract_contact_info

# Unregister the default User model
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + (
        "mongo_role",
        "resume_email",
        "resume_phone",
        "mongo_last_seen",
        "mongo_data_link",
    )

    def _latest_resume_contact(self, obj):
        db = get_db()
        resume_doc = db["resumes"].find_one(
            {"user_id": obj.id},
            sort=[("created_at", -1)],
            projection={"contact": 1, "raw_text": 1},
        )
        if not resume_doc:
            return {"email": "Not available", "phone": "Not mentioned in resume"}

        contact = resume_doc.get("contact") if isinstance(resume_doc.get("contact"), dict) else {}
        if not contact.get("email") or not contact.get("phone"):
            raw_text = str(resume_doc.get("raw_text", ""))
            parsed = extract_contact_info(raw_text) if raw_text else {}
            if not contact.get("email"):
                contact["email"] = parsed.get("email")
            if not contact.get("phone"):
                contact["phone"] = parsed.get("phone")

        email = str(contact.get("email", "")).strip()
        phone = str(contact.get("phone", "")).strip()
        return {
            "email": email if email and email != "Not found" else "Not available",
            "phone": phone if phone and phone != "Not found" else "Not mentioned in resume",
        }

    def mongo_role(self, obj):
        db = get_db()
        doc = db["users"].find_one({"user_id": obj.id})
        return doc.get("role", "N/A") if doc else "No Mongo Profile"
    mongo_role.short_description = "Role (Mongo)"

    def resume_email(self, obj):
        return self._latest_resume_contact(obj)["email"]
    resume_email.short_description = "Resume Email"

    def resume_phone(self, obj):
        return self._latest_resume_contact(obj)["phone"]
    resume_phone.short_description = "Resume Phone"

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
