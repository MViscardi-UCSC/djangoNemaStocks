import django_tables2 as tables
from .models import Strain, Tube, Box, FreezeGroup, ThawRequest, FreezeRequest
from django.utils.html import format_html

class StrainTable(tables.Table):
    selected = tables.CheckBoxColumn(accessor='pk', orderable=False)
    formatted_wja = tables.Column(linkify=True, verbose_name='WJA')
    description = tables.Column()
    date_created = tables.Column()
    phenotype = tables.Column()
    
    class Meta:
        model = Strain
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'formatted_wja', 'genotype', 'date_created', 'phenotype')


class TubeTable(tables.Table):  # CURRENTLY UNUSED
    selected = tables.CheckBoxColumn(accessor='pk', orderable=False)
    strain = tables.Column(linkify=lambda record: record.strain.get_absolute_url(),
                           accessor='strain.formatted_wja', verbose_name='WJA')
    box = tables.Column(linkify=False)
    freeze_group = tables.Column(linkify=False)
    thaw_requester = tables.Column(linkify=False)
    thawed = tables.Column()
    date_created = tables.Column()
    date_thawed = tables.Column()
    
    class Meta:
        model = Tube
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'strain', 'box', 'freeze_group', 'thaw_requester', 'thawed', 'date_created', 'date_thawed')


class FreezeGroupTable(tables.Table):
    selected = tables.CheckBoxColumn(accessor='pk', orderable=False)
    date_created = tables.Column()
    tester_initials = tables.Column()
    tester_comments = tables.Column()
    active_tubes_count = tables.Column(verbose_name='Active Tubes')
    
    class Meta:
        model = FreezeGroup
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'date_created', 'tester',
                  'tester_comments', 'active_tubes_count')


class MiniFreezeGroupTable(tables.Table):
    date_created = tables.Column()
    tester_comments = tables.Column()
    active_tubes_count = tables.Column(verbose_name='Active Tubes')

    class Meta:
        model = FreezeGroup
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('date_created', 'tester',
                  'tester_comments', 'active_tubes_count')


class FreezeRequestTable(tables.Table):
    selected = tables.CheckBoxColumn(accessor='pk', orderable=False)
    date_created = tables.Column()
    requester = tables.Column()
    strain = tables.Column(linkify=lambda record: record.strain.get_absolute_url(),
                           accessor='strain.formatted_wja', verbose_name='WJA')
    number_of_tubes = tables.Column()
    cap_color = tables.Column()
    status = tables.Column()
    
    class Meta:
        model = FreezeRequest
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'date_created', 'requester', 'strain',
                  'number_of_tubes', 'cap_color', 'status')

class ThawRequestTable(tables.Table):
    selected = tables.CheckBoxColumn(accessor='pk', orderable=False)
    date_created = tables.Column()
    strain = tables.Column(linkify=lambda record: record.strain.get_absolute_url(),
                           accessor='strain.formatted_wja', verbose_name='WJA')
    requester = tables.Column()
    request_comments = tables.Column()
    status = tables.Column()
    
    class Meta:
        model = ThawRequest
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'date_created', 'strain', 'requester', 'request_comments', 'status')


class MiniThawRequestTable(tables.Table):
    date_created = tables.Column()
    requester = tables.Column()
    requester_comments = tables.Column()
    status = tables.Column()

    class Meta:
        model = ThawRequest
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('date_created', 'requester', 'requester_comments', 'date_completed')
