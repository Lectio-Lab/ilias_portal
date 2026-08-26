from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import IliasCredential, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(IliasCredential)
class IliasCredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "ilias_username", "created_at", "updated_at")
    search_fields = ("user__email", "ilias_username")
    readonly_fields = ("ilias_password", "phpsessid", "shibsession", "created_at", "updated_at")
    exclude = ()
    # ilias_password is legacy and must remain blank; do not expose an editable password widget.
    readonly_fields = ("created_at", "updated_at")
