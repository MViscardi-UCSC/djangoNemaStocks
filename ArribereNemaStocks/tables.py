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
        fields = ('selected', 'formatted_wja', 'description', 'date_created', 'phenotype')


class TubeTable(tables.Table):
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
    formatted_wja = tables.Column(linkify=True, verbose_name='WJA')
    date_created = tables.Column()
    date_thawed = tables.Column()
    thawed = tables.Column()
    thaw_requester = tables.Column()
    
    class Meta:
        model = FreezeGroup
        # template_name = 'django_tables2/bootstrap4.html'
        fields = ('selected', 'formatted_wja', 'date_created', 'date_thawed', 'thawed', 'thaw_requester')