from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import IliasCredential, User


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        return token


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "created_at", "updated_at")
        read_only_fields = ("id", "email", "created_at", "updated_at")


class IliasCredentialSerializer(serializers.ModelSerializer):
    ilias_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = IliasCredential
        fields = ("ilias_username", "ilias_password", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        credential, _ = IliasCredential.objects.update_or_create(
            user=user,
            defaults={
                "ilias_username": validated_data["ilias_username"],
                "ilias_password": validated_data["ilias_password"],
            },
        )
        return credential

    def update(self, instance, validated_data):
        instance.ilias_username = validated_data.get(
            "ilias_username", instance.ilias_username
        )
        instance.ilias_password = validated_data.get(
            "ilias_password", instance.ilias_password
        )
        instance.save()
        return instance
