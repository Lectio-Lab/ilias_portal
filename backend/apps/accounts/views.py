from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import IliasCredential
from .serializers import (
    IliasCredentialSerializer,
    MyTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        # Embed custom claims
        refresh["email"] = user.email
        refresh["first_name"] = user.first_name
        refresh["last_name"] = user.last_name

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class IliasCredentialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            credential = request.user.ilias_credential
        except IliasCredential.DoesNotExist:
            return Response(
                {"detail": "No ILIAS credentials saved yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Never return the password on GET
        return Response(
            {
                "ilias_username": credential.ilias_username,
                "created_at": credential.created_at,
                "updated_at": credential.updated_at,
            }
        )

    def post(self, request):
        serializer = IliasCredentialSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        credential = serializer.save()
        return Response(
            {
                "ilias_username": credential.ilias_username,
                "created_at": credential.created_at,
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        try:
            credential = request.user.ilias_credential
        except IliasCredential.DoesNotExist:
            return Response(
                {"detail": "No ILIAS credentials found. Use POST to create first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = IliasCredentialSerializer(
            credential, data=request.data, partial=True, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        credential = serializer.save()
        return Response(
            {
                "ilias_username": credential.ilias_username,
                "updated_at": credential.updated_at,
            }
        )
