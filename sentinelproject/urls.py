"""
URL configuration for sentinelproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from sentinelapi.views.user import UserViewSet
from sentinelapi.views.student import StudentViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"students", StudentViewSet, basename="student")

urlpatterns = [
    path("login", UserViewSet.as_view({"post": "user_login"}), name="login"),
    path(
        "register", UserViewSet.as_view({"post": "register_account"}), name="register"
    ),
    path("me", UserViewSet.as_view({"get": "me"}), name="me"),
    path("", include(router.urls)),
    path("admin/", admin.site.urls),
]
