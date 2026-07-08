import urllib.parse

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import IliasCredential

from .client import IliasClient, IliasLoginError
from .models import CourseCache
from .serializers import (
    CourseCacheSerializer,
    CourseContentsSerializer,
    PublishAnnouncementSerializer,
    PublishAssignmentSerializer,
)


def _get_ilias_client(user) -> IliasClient:
    """
    Retrieve the user's saved ILIAS credentials and return a logged-in IliasClient.
    Raises ValueError / IliasLoginError on failure.
    """
    try:
        creds = user.ilias_credential
    except IliasCredential.DoesNotExist:
        raise ValueError(
            "No ILIAS credentials saved. Please add them via /api/auth/ilias-credentials/"
        )

    client = IliasClient(
        username=creds.ilias_username,
        password=creds.ilias_password,
        phpsessid=creds.phpsessid,
        shibsession=creds.shibsession,
    )
    client.login()

    # Cache the updated cookies back to the database if they changed
    if client.phpsessid != creds.phpsessid or client.shibsession != creds.shibsession:
        creds.phpsessid = client.phpsessid
        creds.shibsession = client.shibsession
        creds.save(update_fields=["phpsessid", "shibsession"])

    return client


class RefreshCoursesView(APIView):
    """POST /api/ilias/courses/refresh/ — login, scrape dashboard, persist to cache."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error during login: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            courses = client.get_dashboard_courses()
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to fetch courses: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Persist / update course cache
        saved = []
        for course in courses:
            obj, _ = CourseCache.objects.update_or_create(
                user=request.user,
                course_id=course["id"],
                defaults={
                    "title": course.get("title", ""),
                    "url": course.get("url", ""),
                    "role": course.get("role", ""),
                },
            )
            saved.append(obj)

        serializer = CourseCacheSerializer(saved, many=True)
        return Response(
            {"count": len(saved), "courses": serializer.data},
            status=status.HTTP_200_OK,
        )


class CoursesView(APIView):
    """GET /api/ilias/courses/ — return cached courses from DB."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = CourseCache.objects.filter(user=request.user)
        serializer = CourseCacheSerializer(courses, many=True)
        return Response({"count": courses.count(), "courses": serializer.data})


class CourseContentsView(APIView):
    """GET /api/ilias/courses/<course_id>/contents/ — fetch live course contents."""

    permission_classes = [IsAuthenticated]

    def get(self, request, course_id: int):
        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            contents = client.get_course_contents(course_id)
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to fetch course contents: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        serializer = CourseContentsSerializer(contents)
        return Response(serializer.data)


class PublishAssignmentView(APIView):
    """POST /api/ilias/courses/<course_id>/publish/assignment/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id: int):
        serializer = PublishAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = serializer.validated_data
        filename = ""
        file_content = None
        content_type = "application/octet-stream"

        # Support optional file upload via multipart
        if "file" in request.FILES:
            uploaded = request.FILES["file"]
            filename = uploaded.name
            file_content = uploaded.read()
            content_type = uploaded.content_type or "application/octet-stream"

        try:
            url = client.publish_assignment(
                course_id=course_id,
                title=data["title"],
                instruction=data["instruction"],
                deadline=data.get("deadline") or None,
                filename=filename,
                file_content=file_content,
                content_type=content_type,
            )
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as exc:
            return Response(
                {"detail": f"Failed to publish assignment: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"url": url}, status=status.HTTP_201_CREATED)


class PublishSlidesView(APIView):
    """POST /api/ilias/courses/<course_id>/publish/slides/ — multipart form upload."""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id: int):
        title = request.data.get("title", "").strip()
        if not title:
            return Response(
                {"detail": "title is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        description = request.data.get("description", "")

        # Collect uploaded files
        files = []
        for key, uploaded in request.FILES.items():
            files.append(
                {
                    "filename": uploaded.name,
                    "content": uploaded.read(),
                    "content_type": uploaded.content_type or "application/octet-stream",
                    "title": uploaded.name,
                    "description": "",
                }
            )

        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            url = client.publish_slides(
                course_id=course_id,
                title=title,
                description=description,
                files=files,
            )
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as exc:
            return Response(
                {"detail": f"Failed to publish slides: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"url": url}, status=status.HTTP_201_CREATED)


class PublishAnnouncementView(APIView):
    """POST /api/ilias/courses/<course_id>/publish/announcement/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id: int):
        serializer = PublishAnnouncementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = serializer.validated_data
        try:
            url = client.publish_announcement(
                course_id=course_id,
                title=data["title"],
                content=data["content"],
                visibility=data.get("visibility", "users"),
            )
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as exc:
            return Response(
                {"detail": f"Failed to publish announcement: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"url": url}, status=status.HTTP_201_CREATED)


class DownloadFileView(APIView):
    """
    GET /api/ilias/download/?url=<encoded_ilias_url>
    Proxies the file download through the user's ILIAS session.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_url = request.query_params.get("url", "").strip()
        if not raw_url:
            return Response(
                {"detail": "Query parameter 'url' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decode if URL-encoded
        file_url = urllib.parse.unquote(raw_url)

        try:
            client = _get_ilias_client(request.user)
        except (ValueError, IliasLoginError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            content = client.download_file(file_url)
        except IliasLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to download file: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Attempt to derive a filename from the URL
        parsed = urllib.parse.urlparse(file_url)
        path_segments = parsed.path.rstrip("/").split("/")
        filename = path_segments[-1] if path_segments else "download"

        response = HttpResponse(content, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(content)
        return response
