from django.contrib import admin

# Register your models here.
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'initials')
    list_filter = ('role', 'initials')
    search_fields = ('user', 'role', 'initials')