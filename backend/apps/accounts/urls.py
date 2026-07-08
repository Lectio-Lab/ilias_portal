from django.urls import path

from .views import IliasCredentialView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("ilias-credentials/", IliasCredentialView.as_view()),
]
