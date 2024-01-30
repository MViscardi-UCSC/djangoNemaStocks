from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from simple_history import register as register_history
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib import messages

# Register your models here.
from .models import UserProfile, StrainRange, OpenRegistration

admin.site.register(OpenRegistration)

# register_history(User)
register_history(Group)


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

class StrainRangeInline(admin.TabularInline):
    model = StrainRange
    extra = 0
    autocomplete_fields = ['user_profile']

@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'role', 'initials', 'active_status')
    list_filter = ('role', 'initials', 'active_status')
    search_fields = ('user__username', 'role', 'initials')
    
    actions = ['mark_active', 'mark_inactive']
    
    inlines = [StrainRangeInline]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserProfileAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('user',)
        return readonly_fields
    
    @admin.action(description="Mark selected user profiles as active")
    def mark_active(self, request, queryset):
        queryset.update(active_status=True)
        messages.success(request, f"Marked selected user profiles as active {request.user}")
    
    @admin.action(description="Mark selected user profiles as inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(active_status=False)
        messages.success(request, f"Marked selected user profiles as inactive {request.user}")


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False
    autocomplete_fields = ['user']


class ActiveStatusFilter(admin.SimpleListFilter):
    title = 'active status'  # Human-readable title which will be displayed in the right admin sidebar just above the filter options.
    parameter_name = 'active_status'  # Parameter for the filter that will be used in the URL query.

    def lookups(self, request, model_admin):
        # List of values to allow admin to select.
        return [
            ('True', 'Active Nemastocks Users'),
            ('False', 'Inactive Nemastocks Users'),
        ]

    def queryset(self, request, queryset):
        # Returns the filtered queryset based on the value provided in the query string.
        if self.value() == 'True':
            return queryset.filter(userprofile__active_status=True)
        elif self.value() == 'False':
            return queryset.filter(userprofile__active_status=False)


admin.site.unregister(User)
@admin.register(User)
class UserAdmin(SimpleHistoryAdmin, DefaultUserAdmin):
    list_display = ('username', 'initials', 'email', 'is_staff', 'active_status')
    list_filter = (ActiveStatusFilter, 'is_staff', 'is_superuser', 'groups')
    
    actions = ['give_request_permissions']
    
    inlines = [UserProfileInline, ]
    
    def initials(self, obj):
        return obj.userprofile.initials
    initials.short_description = 'Initials'
    
    def active_status(self, obj):
        return obj.userprofile.active_status
    active_status.short_description = 'Active Status'
    active_status.boolean = True
    
    @admin.action(description="Give selected users request permissions")
    def give_request_permissions(self, request, queryset):
        group = Group.objects.get(name='requesters')
        for user in queryset:
            user.groups.add(group)
        messages.success(request, f"Gave selected users request permissions {request.user}")
    
