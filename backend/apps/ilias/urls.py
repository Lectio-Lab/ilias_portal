from django.urls import path

from .views import (
    CourseContentsView,
    CoursesView,
    DownloadFileView,
    PublishAnnouncementView,
    PublishAssignmentView,
    PublishSlidesView,
    RefreshCoursesView,
)

urlpatterns = [
    path("courses/", CoursesView.as_view()),
    path("courses/refresh/", RefreshCoursesView.as_view()),
    path("courses/<int:course_id>/contents/", CourseContentsView.as_view()),
    path(
        "courses/<int:course_id>/publish/assignment/", PublishAssignmentView.as_view()
    ),
    path("courses/<int:course_id>/publish/slides/", PublishSlidesView.as_view()),
    path(
        "courses/<int:course_id>/publish/announcement/",
        PublishAnnouncementView.as_view(),
    ),
    path("download/", DownloadFileView.as_view()),
]
