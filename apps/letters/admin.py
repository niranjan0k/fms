from django.contrib import admin
from .models import Letter

@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ("reference_no", "title", "status", "current_holder", "created_at")
    search_fields = ("reference_no", "title")
    list_filter = ("status",)
    readonly_fields = ("reference_no", "status", "created_at", "updated_at")
