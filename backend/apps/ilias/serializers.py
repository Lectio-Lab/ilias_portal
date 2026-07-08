from rest_framework import serializers

from .models import CourseCache


class CourseCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCache
        fields = ("course_id", "title", "url", "role", "last_refreshed")
        read_only_fields = fields


class CourseItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.URLField()
    type = serializers.CharField(allow_null=True, default=None)
    properties = serializers.DictField(child=serializers.CharField(), default=dict)


class CourseSectionSerializer(serializers.Serializer):
    section = serializers.CharField()
    items = CourseItemSerializer(many=True)


class CourseContentsSerializer(serializers.Serializer):
    course_title = serializers.CharField(allow_null=True)
    sections = CourseSectionSerializer(many=True)


class PublishAssignmentSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=500)
    instruction = serializers.CharField()
    deadline = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Deadline in DD.MM.YYYY HH:MM format (ILIAS locale).",
    )


class PublishAnnouncementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=500)
    content = serializers.CharField()
    visibility = serializers.ChoiceField(
        choices=["users", "public"], default="users", required=False
    )
