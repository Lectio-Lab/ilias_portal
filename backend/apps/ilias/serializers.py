from datetime import datetime

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


class EditExerciseSerializer(serializers.Serializer):
    exercise_url = serializers.URLField()
    expected_title = serializers.CharField(max_length=500)
    expected_description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    expected_assignment_title = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )
    expected_instruction = serializers.CharField(required=False, allow_blank=True)
    expected_deadline = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    title = serializers.CharField(
        max_length=500, required=False, allow_blank=False
    )
    description = serializers.CharField(required=False, allow_blank=True)
    assignment_id = serializers.IntegerField(required=False, min_value=1)
    assignment_title = serializers.CharField(
        max_length=500, required=False, allow_blank=False
    )
    instruction = serializers.CharField(required=False, allow_blank=True)
    deadline = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Deadline in DD.MM.YYYY HH:MM format; blank removes the deadline.",
    )

    def validate(self, attrs):
        editable_fields = (
            "title",
            "description",
            "assignment_title",
            "instruction",
            "deadline",
        )
        if not any(field in attrs for field in editable_fields):
            raise serializers.ValidationError(
                "Provide at least one field to edit: " + ", ".join(editable_fields)
            )
        expected_pairs = (
            ("description", "expected_description"),
            ("assignment_title", "expected_assignment_title"),
            ("instruction", "expected_instruction"),
            ("deadline", "expected_deadline"),
        )
        missing = [
            expected
            for replacement, expected in expected_pairs
            if replacement in attrs and expected not in attrs
        ]
        if missing:
            raise serializers.ValidationError(
                "Provide the current value from item discovery before editing: "
                + ", ".join(missing)
            )
        return attrs

    def validate_deadline(self, value):
        if not value:
            return value
        try:
            datetime.strptime(value, "%d.%m.%Y %H:%M")
        except ValueError as exc:
            raise serializers.ValidationError(
                "Use DD.MM.YYYY HH:MM, or an empty string to remove the deadline."
            ) from exc
        return value

    def validate_expected_deadline(self, value):
        if value is None:
            return value
        return self.validate_deadline(value)


class GradeTargetSerializer(serializers.Serializer):
    exercise_url = serializers.URLField()
    assignment_id = serializers.IntegerField(min_value=1)
    participant_login = serializers.CharField(max_length=255)


class PostGradeSerializer(GradeTargetSerializer):
    expected_exercise_title = serializers.CharField(max_length=500)
    expected_assignment_title = serializers.CharField(max_length=500)
    expected_status = serializers.ChoiceField(
        choices=["notgraded", "passed", "failed"]
    )
    expected_mark = serializers.CharField(max_length=32, allow_blank=True)
    expected_comment = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(
        choices=["notgraded", "passed", "failed"], required=False
    )
    mark = serializers.CharField(max_length=32, allow_blank=True, required=False)
    comment = serializers.CharField(allow_blank=True, required=False)

    def validate(self, attrs):
        if not any(field in attrs for field in ("status", "mark", "comment")):
            raise serializers.ValidationError(
                "Provide at least one grade field to update: status, mark, or comment."
            )
        return attrs
