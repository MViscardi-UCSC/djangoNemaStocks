from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from simple_history.models import HistoricalRecords
from auditlog.models import AuditlogHistoryField

from hardcoded import CAP_COLOR_OPTIONS


class StrainManager(models.Manager):
    def get_by_natural_key(self, wja):
        return self.get(wja=wja)

    def search(self, query):
        return self.filter(
            Q(formatted_wja__icontains=query) |
            Q(phenotype__icontains=query) |
            Q(genotype__icontains=query)
            # Add other fields as needed
        )
    
    def deep_search(self, query):
        return self.filter(
            Q(formatted_wja__icontains=query) |
            Q(description__icontains=query) |
            Q(phenotype__icontains=query) |
            Q(genotype__icontains=query) |
            Q(source__icontains=query) |
            Q(additional_comments__icontains=query)
            # Add other fields as needed
        )


class OpenStrainEditing(models.Model):
    editing_levels = (
        ('A', 'Edit Any Strains'),
        ('O', 'Edit Own Strains'),
        ('N', 'No Editing Permissions'),
    )
    edit_ability = models.CharField(max_length=1, choices=editing_levels, default='N')
    
    audit_history = AuditlogHistoryField()

    def get_edit_ability_display(self):
        return dict(self.editing_levels).get(self.edit_ability, 'Unknown')
    
    def __repr__(self):
        return f'Strain Editing Permissions: {self.get_edit_ability_display()}'
    
    def __str__(self):
        return self.__repr__()


class Strain(models.Model):
    wja = models.IntegerField(unique=True)
    genotype = models.CharField(max_length=255, null=True, blank=True, editable=True)
    date_created = models.DateField(default=timezone.now, editable=True)
    phenotype = models.TextField(null=True, blank=True, editable=True)
    description = models.TextField(null=True, blank=True, editable=True)
    formatted_wja = models.CharField(max_length=8, editable=False)
    source = models.CharField(max_length=255, null=True, blank=True, editable=True)
    additional_comments = models.TextField(null=True, blank=True, editable=True)
    
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()
    
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

    def get_owner_from_ranges(self):
        """
        This method returns the owner of the strain based on the ranges of strains that they own.
        :return: The owner of the strain.
        """
        from profiles.models import StrainRange
        for strain_range in StrainRange.objects.all():
            if strain_range.check_if_strain_in_range(self):
                return strain_range.user_profile
        return None

    def latest_freeze_group(self):
        return self.freeze_groups.latest('date_created')


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
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()
    
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
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()

    class Meta:
        unique_together = ('dewar', 'rack', 'box')
        verbose_name_plural = 'Boxes'
    
    def is_default_box(self):
        return DefaultBox.objects.filter(box=self).exists()
    
    def short_pos_repr(self):
        return f'JA{self.dewar:0>2}-R{self.rack:0>2}-B{self.box:0>2}'
    
    def __repr__(self):
        is_default = 'Active' if self.is_default_box() else ''
        return f'{is_default}Box({self.short_pos_repr()}; {self.get_usage_str()})'

    def repr(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()
    
    def get_active_tubes(self):
        return self.tube_set.filter(thawed=False)
    
    def get_usage_str(self, max_tubes_per_box=81):
        return f'{self.get_active_tubes().count():0>2}/{max_tubes_per_box}'
    
    def is_full(self, max_tubes_per_box=81) -> bool:
        return self.get_active_tubes().count() >= max_tubes_per_box


class DefaultBox(models.Model):
    """
    This model is used to store the box for each dewar that tubes are placed in by default.
    """
    box = models.ForeignKey('Box', on_delete=models.CASCADE)
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()

    class Meta:
        verbose_name_plural = 'DefaultBoxes'
    
    def clean(self):
        # Check if there is already a DefaultBox for the same dewar
        if DefaultBox.objects.filter(box__dewar=self.box.dewar).exclude(pk=self.pk).exists():
            raise ValidationError(f"A default box for dewar {self.box.dewar} already exists.")

    @classmethod
    def get_default_box_for_dewar(cls, dewar: int) -> 'DefaultBox':
        try:
            return cls.objects.get(box__dewar=dewar)
        except cls.DoesNotExist:
            return None

    def __repr__(self):
        return f'DefaultBox({self.box.short_pos_repr()}; {self.box.get_usage_str()})'

    def repr(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()


class FreezeGroup(models.Model):
    date_created = models.DateField(default=timezone.now, editable=True)
    date_stored = models.DateField(null=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE,
                               related_name='freeze_groups')
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
    
    freeze_request = models.OneToOneField('FreezeRequest', on_delete=models.CASCADE, null=True, blank=True)
    
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()

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
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()
    
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
    
    simp_history = HistoricalRecords()
    audit_history = AuditlogHistoryField()
    
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
    
    def strain_recently_failed_freeze(self, days=365):
        failed_freezes = FreezeGroup.objects.filter(
            strain=self.strain,
            passed_test=False,
            date_created__gte=timezone.now() - timezone.timedelta(days=days),
        )
        successful_freezes = FreezeGroup.objects.filter(
            strain=self.strain,
            passed_test=True,
            date_created__gte=timezone.now() - timezone.timedelta(days=days),
        )
        # Now we need to return True if:
        #  1. There was >=1 fail and no successes
        #  2. The most recent fail was more recent than the most recent success
        if failed_freezes.count() > 0 and successful_freezes.count() == 0:
            print(f'The strain targeted by FreezeRequest({self.id}) [{self.strain.formatted_wja}] '
                  f'has recently failed a freeze request.')
            return True
        elif failed_freezes.count() > 0 and successful_freezes.count() > 0:
            latest_fail = failed_freezes.latest('date_created')
            latest_success = successful_freezes.latest('date_created')
            if latest_fail.date_created > latest_success.date_created:
                print(f'The strain targeted by FreezeRequest({self.id}) [{self.strain.formatted_wja}] '
                      f'was recently attempted to be frozen but it failed. '
                      f'There is a successful freeze request but that was '
                      f'before the failed attempt.')
                return True
            else:
                print(f'The strain targeted by FreezeRequest({self.id}) [{self.strain.formatted_wja}] '
                      f'was recently attempted to be frozen but it failed. '
                      f'There is a successful freeze request and that was '
                      f'more recent than the failed attempt.')
                return False
        else:
            print(f"The strain targeted by FreezeRequest({self.id}) [{self.strain.formatted_wja}] "
                  f"has not been the target of any recent freeze requests that have failed.")
            return False
    
    def is_a_refreeze(self):
        return self.strain_recently_failed_freeze()
