from django.urls import path

from .views import (
    CourseContentsView,
    CoursesView,
    DownloadFileView,
    EditExerciseView,
    FindCourseItemsView,
    GradeTargetView,
    PostGradeView,
    PublishAnnouncementView,
    PublishAssignmentView,
    PublishSlidesView,
    RefreshCoursesView,
    SessionStatusView,
)

urlpatterns = [
    path("courses/", CoursesView.as_view()),
    path("courses/refresh/", RefreshCoursesView.as_view()),
    path("session/status/", SessionStatusView.as_view()),
    path("courses/<int:course_id>/contents/", CourseContentsView.as_view()),
    path(
        "courses/<int:course_id>/items/search/", FindCourseItemsView.as_view()
    ),
    path(
        "courses/<int:course_id>/items/exercise/", EditExerciseView.as_view()
    ),
    path(
        "courses/<int:course_id>/grades/target/", GradeTargetView.as_view()
    ),
    path("courses/<int:course_id>/grades/", PostGradeView.as_view()),
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
