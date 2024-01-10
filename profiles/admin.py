from django.contrib import admin

# Register your models here.
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'initials')
    list_filter = ('role', 'initials')
    search_fields = ('user__username', 'role', 'initials')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserProfileAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('user',)
        return readonly_fields
