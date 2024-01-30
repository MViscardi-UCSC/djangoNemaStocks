from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from datetime import datetime

from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
from .models import Strain, Tube, Box, FreezeGroup, ThawRequest, FreezeRequest

admin.site.site_header = 'Arribere Lab NemaStocks Database'


@admin.register(Tube)
class TubeAdmin(SimpleHistoryAdmin):
    @admin.action(description="Mark selected tubes as thawed")
    def thaw_tubes(self, request, queryset):
        queryset.update(thawed=True)
        updated = queryset.update(date_thawed=datetime.now())
        self.message_user(
            request,
            ngettext(
                "%d tube was successfully marked as thawed.",
                "%d tubes were successfully marked as thawed.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Mark selected tubes as unthawed")
    def unthaw_tubes(self, request, queryset):
        queryset.update(thawed=False)
        updated = queryset.update(date_thawed=None)
        self.message_user(
            request,
            ngettext(
                "%d tube was successfully marked as not thawed.",
                "%d tubes were successfully marked as not thawed.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    list_display = ('id', 'strain', 'cap_color', 'date_created', 'date_thawed',
                    'box', 'freeze_group', 'thawed', 'thaw_requester')
    list_filter = ('date_created', 'date_thawed', 'thawed', 'thaw_requester', 'cap_color')
    search_fields = ('date_created', 'date_thawed', 'strain__wja',
                     'thawed', 'thaw_requester')
    actions = [thaw_tubes, unthaw_tubes]

    autocomplete_fields = ['strain', 'box', 'freeze_group']

class TubeInline(admin.TabularInline):
    model = Tube
    extra = 0
    autocomplete_fields = ['strain', 'box', 'freeze_group']


@admin.register(Box)
class BoxAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'dewar', 'rack', 'box', 'active_tubes')
    list_filter = ('dewar', 'rack', 'box')
    search_fields = ('dewar', 'rack', 'box')
    
    inlines = [TubeInline,]
    
    def active_tubes(self, obj):
        return obj.get_active_tubes().count()
    active_tubes.short_description = 'Active Tubes'


@admin.register(FreezeGroup)
class FreezeGroupAdmin(SimpleHistoryAdmin):
    @admin.action(description="Mark selected freezes with 'Test Started'")
    def mark_test_started(self, request, queryset):
        queryset.update(started_test=True)

    @admin.action(description="Unmark selected freezes with 'Test Started'")
    def unmark_test_started(self, request, queryset):
        queryset.update(started_test=False)

    @admin.action(description="Mark selected freezes with 'Test Completed'")
    def mark_test_completed(self, request, queryset):
        queryset.update(completed_test=True)
    
    @admin.action(description="Unmark selected freezes with 'Test Completed'")
    def unmark_test_completed(self, request, queryset):
        queryset.update(completed_test=False)

    @admin.action(description="Mark selected freezes with 'Test Passed'")
    def mark_test_passed(self, request, queryset):
        queryset.update(passed_test=True)

    @admin.action(description="Unmark selected freezes with 'Test Passed'")
    def unmark_test_passed(self, request, queryset):
        queryset.update(passed_test=False)

    @admin.action(description="Mark selected freezes with 'Stored'")
    def mark_stored(self, request, queryset):
        queryset.update(stored=True)

    @admin.action(description="Unmark selected freezes with 'Stored'")
    def unmark_stored(self, request, queryset):
        queryset.update(stored=False)

    list_display = ('id', 'strain', 'freezer',
                    'started_test', 'completed_test', 'passed_test', 'stored',
                    'tester', 'tester_comments')
    list_filter = ('freezer',
                   'started_test', 'completed_test', 'passed_test',
                   'stored', 'tester')
    search_fields = ('strain__wja',
                     'tester_comments', 'tester')
    actions = [mark_test_started, unmark_test_started,
               mark_test_completed, unmark_test_completed,
               mark_test_passed, unmark_test_passed,
               mark_stored, unmark_stored]

    inlines = [TubeInline, ]

class FreezeGroupInline(admin.TabularInline):
    model = FreezeGroup
    extra = 0
    autocomplete_fields = ['strain']

class FreezeGroupInlineS(admin.StackedInline):
    model = FreezeGroup
    extra = 0
    autocomplete_fields = ['strain']

@admin.register(ThawRequest)
class ThawRequestAdmin(SimpleHistoryAdmin):
    
    @admin.action(description="Mark selected thaw requests as completed")
    def mark_completed(self, request, queryset):
        queryset.update(completed=True)
        queryset.update(date_completed=datetime.now())
        messages.success(request, f"Marked selected thaw requests as completed {request.user}")

    @admin.action(description="Unmark selected thaw requests as completed")
    def unmark_completed(self, request, queryset):
        queryset.update(completed=False)
        queryset.update(date_completed=None)

    list_display = ('id', 'strain', 'date_created', 'requester',
                    'is_urgent', 'status', 'thawed_by', 'request_comments')
    list_filter = ('date_created', 'date_completed',
                   'status', 'requester', 'thawed_by')
    search_fields = ('date_completed', 'status', 'thawed_by', 'strain__wja',
                     )
    actions = [mark_completed, unmark_completed]


# admin.site.register(FreezeRequest)
@admin.register(FreezeRequest)
class FreezeRequestAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'strain', 'date_created', 'requester',
                    'number_of_tubes', 'cap_color', 'status')
    list_filter = ('date_created', 'status', 'requester', 'cap_color')
    search_fields = ('date_created', 'status', 'requester', 'strain__wja',
                     'cap_color', 'number_of_tubes')
    
    inlines = [FreezeGroupInlineS, ]


@admin.register(Strain)
class StrainAdmin(SimpleHistoryAdmin):
    list_display = ('formatted_wja', 'description', 'date_created',
                    'phenotype', 'active_tubes_count', 'inactive_tubes_count')
    # list_filter = ('date_created', 'wja')
    search_fields = ('wja', 'date_created')
    ordering = ('wja',)
    inlines = [FreezeGroupInline, ]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(StrainAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('wja', 'formatted_wja',)
        return readonly_fields

    def active_tubes_count(self, obj):
        return obj.active_tubes_count()

    active_tubes_count.short_description = 'Active Tubes'

    def inactive_tubes_count(self, obj):
        return obj.inactive_tubes_count()

    inactive_tubes_count.short_description = 'Thawed Tubes'
