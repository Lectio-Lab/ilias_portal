from apps.accounts.views import MyTokenObtainPairView
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", MyTokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/ilias/", include("apps.ilias.urls")),
]
