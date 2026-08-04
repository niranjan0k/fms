from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "level", "is_staff")
    list_filter = ("role", "level", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("Workflow", {"fields": ("role", "level")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Workflow", {"fields": ("role", "level")}),)
