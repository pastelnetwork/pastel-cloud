from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.models import User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


# TODO: display image converted from base64 as <img>
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass
