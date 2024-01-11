from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from profiles.models import UserProfile


class StrainManager(models.Manager):
    def get_by_natural_key(self, wja):
        return self.get(wja=wja)
    
    def search(self, query):
        return self.filter(
            Q(formatted_wja__icontains=query) |
            Q(description__icontains=query) |
            Q(phenotype__icontains=query)
            # Add other fields as needed
        )


class Strain(models.Model):
    wja = models.IntegerField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True, editable=True)
    date_created = models.DateField(auto_now_add=True, editable=True)
    phenotype = models.CharField(max_length=255, null=True, blank=True, editable=True)
    formatted_wja = models.CharField(max_length=8, editable=False)
    # additional_comments = models.CharField(max_length=255, null=True, blank=True, editable=True)
    history = HistoricalRecords()
    
    objects = StrainManager()
    
    def get_absolute_url(self):
        return f'/strain_details/{self.wja:0>4}'
    
    def save(self, *args, **kwargs):
        """
        This method overrides the default save method to populate the formatted_wja field.
        No other changes were made to the default save method.
        """
        self.formatted_wja = f'WJA{self.wja:0>4}'
        super().save(*args, **kwargs)
    
    @staticmethod
    def populate_formatted_wja():
        """
        This method populates the formatted WJA field for all pre-existing strains
        :return: 
        """
        for obj in Strain.objects.all():
            obj.formatted_wja = f'WJA{obj.wja:0>4}'
            obj.save()
    
    def active_tubes(self):
        return self.tube_set.filter(thawed=False)
    
    def active_tubes_count(self):
        return self.active_tubes().count()
    
    def inactive_tubes(self):
        return self.tube_set.filter(thawed=True)
    
    def inactive_tubes_count(self):
        return self.inactive_tubes().count()
    
    def total_tubes(self):
        return self.tube_set.all()
    
    def total_tubes_count(self):
        return self.total_tubes().count()
    
    def formatted_WJA(self):
        return f'WJA{self.wja:0>4}'
    
    def __repr__(self):
        return f'Strain(WJA{self.wja:0>4}, ' \
               f'Tubes-{self.active_tubes_count()}/{self.total_tubes_count()})'
    
    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()


class Tube(models.Model):
    cap_color = models.CharField(max_length=50, default='N/A')
    date_created = models.DateField(auto_now_add=True, editable=True)
    date_thawed = models.DateField(null=True, editable=True)
    box = models.ForeignKey('Box', on_delete=models.CASCADE, null=True,
                            related_name='tube_set')
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               # choices=Strain.objects.all(),
                               related_name='tube_set')
    freeze_group = models.ForeignKey('FreezeGroup', on_delete=models.CASCADE, null=True,
                                     related_name='tube_set')
    thawed = models.BooleanField(default=False)
    thaw_requester = models.CharField(max_length=50, null=True)
    history = HistoricalRecords()
    
    def thawed_state(self):
        return 'Thawed' if self.thawed else 'Frozen'
    
    def __repr__(self):
        if self.box:
            location_string = f'Location-JA{self.box.dewar:0>2}-Rack{self.box.rack:0>2}-Box{self.box.box:0>4}'
        else:
            location_string = 'Location-NotStored'
        cap_color_string = f'Cap-{self.cap_color:->6}'

        if not self.thawed:
            return f'Tube(Strain-WJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'DateFrozen-{self.date_created.strftime("%m/%d/%Y")})'
        else:
            formatted_thaw_date = self.date_thawed.strftime("%m/%d/%Y") if self.date_thawed else 'N/A'
            return f'ThawedTube(Strain-WJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'DateFrozen-{self.date_created.strftime("%m/%d/%Y")}, ' \
                   f'DateThawed-{formatted_thaw_date})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()
    
    def short_repr(self):
        if self.box:
            location_string = f'JA{self.box.dewar:0>2}-Rack{self.box.rack:0>2}-Box{self.box.box:0>4}'
        else:
            location_string = 'NotStored'
        cap_color_string = f'Cap{self.cap_color:->7}'

        if not self.thawed:
            return f'Tube(WJA{self.strain.wja:0>4}; ' \
                   f'{location_string}; {cap_color_string})'
        else:
            return f'ThawedTube(WJA{self.strain.wja:0>4}; ' \
                   f'{location_string}; {cap_color_string})'


class Box(models.Model):
    dewar = models.IntegerField()
    rack = models.IntegerField()
    box = models.IntegerField()
    history = HistoricalRecords()

    def __repr__(self):
        return f'Box(JA{self.dewar:0>2}-Rack{self.rack:0>2}-Box{self.box:0>4})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()


class FreezeGroup(models.Model):
    date_created = models.DateField(auto_now_add=True, editable=True)
    date_frozen = models.DateField(null=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE)
    freezer_initials = models.CharField(max_length=15, default='N/A')
    # cap_color = models.CharField(max_length=50, default='N/A')
    started_test = models.BooleanField(default=False)
    completed_test = models.BooleanField(default=False)
    passed_test = models.BooleanField(default=False)
    tester_initials = models.CharField(max_length=15, null=True)
    tester_comments = models.CharField(max_length=255, null=True)
    test_check_date = models.DateField(null=True)
    stored = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __repr__(self):
        return f'FreezeGroup(ID-{self.id:0>6}, Strain-WJA{self.strain.wja}, ' \
               f'Frozen-{self.date_frozen.strftime("%m/%d/%Y") if self.date_frozen else "N/A"})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()

    def active_tubes(self):
        return self.tube_set.filter(thawed=False)

    def active_tubes_count(self):
        return self.active_tubes().count()

    def inactive_tubes(self):
        return self.tube_set.filter(thawed=True)

    def inactive_tubes_count(self):
        return self.inactive_tubes().count()

    def total_tubes(self):
        return self.tube_set.all()

    def total_tubes_count(self):
        return self.total_tubes().count()


class ThawRequestManager(models.Manager):
    def get_by_natural_key(self, wja):
        return self.get(wja=wja)

    def search(self, query):
        return self.filter(
            Q(requester__icontains=query) |
            Q(strain__formatted_wja__icontains=query) |
            Q(request_comments__icontains=query)
            # Add other fields as needed
        )

class ThawRequest(models.Model):
    """
    A thaw request is a request to thaw a strain. It is created by a user, and
    then a tube from that strain is auto assigned. Once the tube is thawed, the
    thaw request is marked as completed and the tube is marked as thawed.
    """
    date_created = models.DateField(auto_now_add=True, editable=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               related_name='thaw_requests')
    tube = models.ForeignKey('Tube', on_delete=models.CASCADE,
                             null=True, blank=True)
    requester = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                  related_name='thaw_requests')
    is_urgent = models.BooleanField(default=False)
    request_comments = models.CharField(max_length=255, null=True, blank=True)
    date_completed = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    thawed_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                  related_name='thawed_tubes',
                                  null=True, blank=True)
    history = HistoricalRecords()
    
    objects = ThawRequestManager()

    def __repr__(self):
        return f'ThawRequest(ID-{self.id:0>6}, Strain-{self.strain.formatted_WJA()}, ' \
               f'Tube-{self.tube.strain.wja if self.tube else "NotYetAssigned"}, ' \
               f'Requester-{self.requester}, ' \
               f'DateCreated-{self.date_created.strftime("%m/%d/%Y")}, ' \
               f'DateCompleted-{self.date_completed.strftime("%m/%d/%Y") if self.date_completed else "N/A"})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()


class FreezeRequestManager(models.Manager):
    def get_by_natural_key(self, wja):
        return self.get(wja=wja)

    def search(self, query):
        return self.filter(
            Q(requester__icontains=query) |
            Q(strain__formatted_wja__icontains=query) |
            Q(request_comments__icontains=query)
            # Add other fields as needed
        )

class FreezeRequest(models.Model):
    date_created = models.DateField(auto_now_add=True, editable=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               related_name='freeze_requests')
    requester = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                  related_name='freeze_requests')
    request_comments = models.CharField(max_length=255, null=True, blank=True)
    date_completed = models.DateField(null=True)
    completed = models.BooleanField(default=False)
    number_of_tubes = models.IntegerField(default=1)
    cap_color = models.CharField(max_length=50, null=True, blank=True)
    freeze_group = models.OneToOneField('FreezeGroup', on_delete=models.CASCADE, null=True)
    history = HistoricalRecords()
    
    objects = FreezeRequestManager()

    def __repr__(self):
        return f'FreezeRequest(ID-{self.id:0>6}, Strain-WJA{self.strain.wja}, ' \
               f'Requester-{self.requester}, ' \
               f'DateCreated-{self.date_created.strftime("%m/%d/%Y")}, ' \
               f'DateCompleted-{self.date_completed.strftime("%m/%d/%Y") if self.date_completed else "N/A"})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()
