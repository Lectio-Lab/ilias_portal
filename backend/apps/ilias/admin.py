from django.contrib import admin

from .models import CourseCache


@admin.register(CourseCache)
class CourseCacheAdmin(admin.ModelAdmin):
    list_display = ("title", "course_id", "user", "role", "last_refreshed")
    list_filter = ("role",)
    search_fields = ("title", "user__email")
    readonly_fields = ("last_refreshed",)
    ordering = ("user", "title")
