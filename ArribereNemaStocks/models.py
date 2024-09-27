from django.db import models
from django.db.models import Q
from django.utils import timezone
from simple_history.models import HistoricalRecords

from hardcoded import CAP_COLOR_OPTIONS


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
    date_created = models.DateField(default=timezone.now, editable=True)
    phenotype = models.CharField(max_length=255, null=True, blank=True, editable=True)
    genotype = models.CharField(max_length=255, null=True, blank=True, editable=True)
    formatted_wja = models.CharField(max_length=8, editable=False)
    additional_comments = models.CharField(max_length=255, null=True, blank=True, editable=True)
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
    cap_color = models.CharField(max_length=50, choices=CAP_COLOR_OPTIONS, default='unknown')
    date_created = models.DateField(default=timezone.now, editable=True)
    box = models.ForeignKey('Box', on_delete=models.CASCADE, null=True,
                            related_name='tube_set')
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               # choices=Strain.objects.all(),
                               related_name='tube_set')
    freeze_group = models.ForeignKey('FreezeGroup', on_delete=models.CASCADE, null=True,
                                     related_name='tube_set')
    set_number = models.IntegerField(default=-1)
    
    thawed = models.BooleanField(default=False)
    date_thawed = models.DateField(null=True, blank=True, editable=True)
    thaw_requester = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE,
                                        related_name='thawed_tubes',
                                        null=True, blank=True)
    history = HistoricalRecords()
    
    class Meta:
        unique_together = ('strain', 'freeze_group', 'box', 'set_number')
    
    def thawed_state(self):
        return 'Thawed' if self.thawed else 'Frozen'

    def __repr__(self):
        if self.box:
            location_string = f'JA{self.box.dewar:0>2}-{self.box.rack:0>2}-{self.box.box:0>2}'
        else:
            location_string = 'NotStored'
        cap_color_string = f'{self.cap_color}'

        if not self.thawed:
            return f'tWJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'Frozen-{self.date_created.strftime("%m/%d/%Y")})'
        else:
            formatted_thaw_date = self.date_thawed.strftime("%m/%d/%Y") if self.date_thawed else 'N/A'
            return f'Thawed-tWJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'Frozen-{self.date_created.strftime("%m/%d/%Y")}, ' \
                   f'Thawed-{formatted_thaw_date})'

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

    class Meta:
        unique_together = ('dewar', 'rack', 'box')
        verbose_name_plural = 'Boxes'

    def __repr__(self):
        return f'Box(JA{self.dewar:0>2}-Rack{self.rack:0>2}-Box{self.box:0>2}; {self.get_usage()})'

    def repr(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()
    
    def short_pos_repr(self):
        return f'JA{self.dewar:0>2}-R{self.rack:0>2}-B{self.box:0>2}'
    
    def get_active_tubes(self):
        return self.tube_set.filter(thawed=False)
    
    def get_usage(self, max_tubes_per_box=81):
        return f'{self.get_active_tubes().count():0>2}/{max_tubes_per_box}'
    
    def is_full(self, max_tubes_per_box=81) -> bool:
        return self.get_active_tubes().count() >= max_tubes_per_box


class FreezeGroup(models.Model):
    date_created = models.DateField(default=timezone.now, editable=True)
    date_stored = models.DateField(null=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE)
    freezer = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE,
                                related_name='freeze_groups',
                                null=True, blank=True)
    # cap_color = models.CharField(max_length=50, default='N/A')
    started_test = models.BooleanField(default=False)
    completed_test = models.BooleanField(default=False)
    passed_test = models.BooleanField(default=False)
    tester = models.ForeignKey('profiles.UserProfile', on_delete=models.SET_NULL,
                               related_name='tested_freeze_groups',
                               null=True, blank=True)
    tester_comments = models.CharField(max_length=255, null=True)
    test_check_date = models.DateField(null=True)
    stored = models.BooleanField(default=False)
    
    freeze_request = models.OneToOneField('FreezeRequest', on_delete=models.CASCADE, null=True)
    
    history = HistoricalRecords()

    # class Meta:
    #     unique_together = ('strain', 'date_stored')

    def __repr__(self):
        return f"FreezeGroup(ID-{self.id if self.id else 'xxxx':0>6}, Strain-{self.strain.formatted_wja}, " \
               f"Frozen-{self.date_stored.strftime('%m/%d/%Y') if self.date_stored else 'N/A'})"

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
    
    # Turns out we don't need this!
    # def create_tubes_from_request(self):
    #     raise NotImplementedError


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
    requester = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE,
                                  related_name='thaw_requests')
    is_urgent = models.BooleanField(default=False)
    request_comments = models.CharField(max_length=255, null=True, blank=True)
    date_completed = models.DateField(null=True, blank=True)
    STATUS_OPTIONS = (
        ('R', 'Requested'),
        ('O', 'Ongoing'),
        ('C', 'Completed'),
        ('X', 'Cancelled'),
    )
    status = models.CharField(max_length=1, choices=STATUS_OPTIONS, default='R')
    completed = models.BooleanField(default=False)
    thawed_by = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE,
                                  related_name='czar_thawed_tubes',
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
            Q(requester__user__icontains=query) |
            Q(strain__formatted_wja__icontains=query) |
            Q(request_comments__icontains=query)
            # Add other fields as needed
        )


class FreezeRequest(models.Model):
    date_created = models.DateField(auto_now_add=True, editable=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               related_name='freeze_requests')
    requester = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE,
                                  related_name='freeze_requests')
    request_comments = models.CharField(max_length=255, null=True, blank=True)
    date_advanced = models.DateField(null=True)
    number_of_tubes = models.IntegerField(default=1)
    cap_color = models.CharField(max_length=50, choices=CAP_COLOR_OPTIONS, null=True, blank=True)
    freeze_group = models.OneToOneField('FreezeGroup', on_delete=models.CASCADE, null=True)
    STATUS_CHOICES = (
        ('R', 'Requested'),
        ('A', 'Advanced/Testing'),
        ('C', 'Completed'),
        ('F', 'Failed'),
        ('X', 'Cancelled'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='R')
    
    # Fields added for the new freeze request form:
    # This will allow things like box choice and number of tubes to be easier to track
    box1 = models.ForeignKey('Box', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='box1_freeze_requests')
    box2 = models.ForeignKey('Box', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='box2_freeze_requests')
    tubes_for_box1 = models.IntegerField(null=True, blank=True)
    tubes_for_box2 = models.IntegerField(null=True, blank=True)
    freezer = models.ForeignKey('profiles.UserProfile', on_delete=models.SET_NULL,
                                related_name='freeze_requests_again',
                                null=True, blank=True)
    tester = models.ForeignKey('profiles.UserProfile', on_delete=models.SET_NULL,
                               related_name='tested_freeze_requests',
                               null=True, blank=True)
    tester_comments = models.CharField(max_length=255, null=True, blank=True)
    
    history = HistoricalRecords()
    
    objects = FreezeRequestManager()

    def advance_to_testing(self):
        self.status = 'A'
        self.date_advanced = timezone.now()
        self.save()

    def __repr__(self):
        return f'FreezeRequest(ID-{self.id:0>6}, Strain-{self.strain.formatted_wja}, ' \
               f'Requester-{self.requester}, ' \
               f'DateCreated-{self.date_created.strftime("%m/%d/%Y")}, ' \
               f'DateAdvanced-{self.date_advanced.strftime("%m/%d/%Y") if self.date_advanced else "N/A"})'

    def repr(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()
