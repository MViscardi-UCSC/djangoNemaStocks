from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from simple_history import register as register_history
from django.contrib.auth.models import User, Group

# Register your models here.
from .models import UserProfile, StrainRange

register_history(User)
register_history(Group)

@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'role', 'initials')
    list_filter = ('role', 'initials')
    search_fields = ('user__username', 'role', 'initials')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserProfileAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('user',)
        return readonly_fields

@admin.register(StrainRange)
class StrainRangeAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'strain_numbers_start', 'strain_numbers_end')
    list_filter = ('user_profile', 'strain_numbers_start', 'strain_numbers_end')
    search_fields = ('user_profile', 'strain_numbers_start', 'strain_numbers_end')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(StrainRangeAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('user_profile',)
        return readonly_fields
