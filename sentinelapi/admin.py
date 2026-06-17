"""Admin for the sentinelapi application."""

from django.contrib import admin

from sentinelapi.models import Instructor

admin.site.register(Instructor)
# Register your models here.
