from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ngettext
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from datetime import datetime

from simple_history.admin import SimpleHistoryAdmin
from simple_history import register as register_history

# Register your models here.
from . import models

admin.site.site_header = 'Arribere Lab NemaStocks Database'

admin.site.register(models.OpenStrainEditing)
register_history(models.OpenStrainEditing)

@admin.register(models.Tube)
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
        
    @admin.display(ordering='strain__wja', description='Strain')
    def strain_link(self, obj):
        url = reverse("admin:ArribereNemaStocks_strain_change", args=[obj.strain.pk])
        return format_html('<a href="{}">{}</a>', url, obj.strain.formatted_wja)
    
    @admin.display(ordering='box__dewar', description='Box')
    def box_link(self, obj):
        url = reverse("admin:ArribereNemaStocks_box_change", args=[obj.box.pk])
        return format_html('<a href="{}">{}</a>', url, obj.box)
    
    @admin.display(ordering='freeze_group', description='Freeze Group')
    def freeze_group_link(self, obj):
        url = reverse("admin:ArribereNemaStocks_freezegroup_change", args=[obj.freeze_group.pk])
        return format_html('<a href="{}">{}</a>', url, obj.freeze_group)
    
    list_display = ('id', 'strain_link', 'cap_color', 'date_created', 'date_thawed',
                    'box_link', 'freeze_group_link', 'thawed', 'thaw_requester')
    list_filter = ('date_created', 'date_thawed', 'thawed', 'thaw_requester', 'cap_color')
    search_fields = ('date_created', 'date_thawed', 'strain__wja',
                     'thawed', 'thaw_requester__initials', 'cap_color',
                     'box__dewar', 'box__rack', 'box__box',
                     'freeze_group__id', 'id',
                     'thaw_requester__user__username',
                     'thaw_requester__user__first_name',
                     'thaw_requester__user__last_name',
                     )
    # list_display_links = ('id', 'strain', 'box', 'freeze_group')
    actions = [thaw_tubes, unthaw_tubes]

    autocomplete_fields = ['strain', 'box', 'freeze_group']


class TubeInline(admin.TabularInline):
    model = models.Tube
    extra = 0
    autocomplete_fields = ['strain', 'box', 'freeze_group']


@admin.register(models.Box)
class BoxAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'dewar', 'rack', 'box', 'active_tubes')
    list_filter = ('dewar', 'rack', 'box')
    search_fields = ('dewar', 'rack', 'box')
    
    inlines = [TubeInline,]
    
    def active_tubes(self, obj):
        return obj.get_active_tubes().count()
    active_tubes.short_description = 'Active Tubes'


@admin.register(models.DefaultBox)
class DefaultBoxAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'box')
    # list_filter = ('box__dewar', 'box__rack', 'box__box')
    # search_fields = ('box__dewar', 'box__rack', 'box__box')


@admin.register(models.FreezeGroup)
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
    
    @admin.display(ordering='strain__wja', description='Strain')
    def strain_link(self, obj):
        url = reverse("admin:ArribereNemaStocks_strain_change", args=[obj.strain.pk])
        return format_html('<a href="{}">{}</a>', url, obj.strain.formatted_wja)
    
    list_display = ('id', 'strain_link', 'freezer',
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
    model = models.FreezeGroup
    extra = 0
    autocomplete_fields = ['strain']
    fields = ('strain', 'active_tube_count', 'thawed_tube_count', 'edit_link')

    readonly_fields = ('active_tube_count', 'thawed_tube_count', 'edit_link')

    def active_tube_count(self, obj):
        return obj.active_tubes_count()

    active_tube_count.short_description = 'Active Tubes'

    def thawed_tube_count(self, obj):
        return obj.inactive_tubes_count()

    thawed_tube_count.short_description = 'Thawed Tubes'
    
    def edit_link(self, obj):
        url = reverse("admin:ArribereNemaStocks_freezegroup_change", args=[obj.pk])
        return format_html('<a href="{}">Edit</a>', url)
    edit_link.short_description = 'Edit Link'


class FreezeGroupInlineS(admin.StackedInline):
    model = models.FreezeGroup
    extra = 0
    autocomplete_fields = ['strain']


@admin.register(models.ThawRequest)
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
@admin.register(models.FreezeRequest)
class FreezeRequestAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'strain', 'date_created', 'requester',
                    'number_of_tubes', 'cap_color', 'status')
    list_filter = ('date_created', 'status', 'requester', 'cap_color')
    search_fields = ('date_created', 'status', 'requester', 'strain__wja',
                     'cap_color', 'number_of_tubes')
    
    inlines = [FreezeGroupInlineS, ]


@admin.register(models.Strain)
class StrainAdmin(SimpleHistoryAdmin):
    list_display = ('formatted_wja', 'genotype', 'date_created',
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
