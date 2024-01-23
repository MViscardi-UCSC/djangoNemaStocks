from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, Group
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User, Group, AbstractUser
from hardcoded import ROLE_CHOICES
from typing import List, Tuple, Union

import ArribereNemaStocks.models as nema_models

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='userprofile')
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='o')
    initials = models.CharField(max_length=4, null=False, blank=False, unique=True)
    other_associated_initials = models.CharField(max_length=100, null=True, blank=True)
    active_status = models.BooleanField(default=False)
    
    history = HistoricalRecords()
    
    def __repr__(self):
        return f'{self.user.username.title()} ({self.initials})'
    
    def __str__(self):
        return self.__repr__()
    
    def get_strains(self) -> Tuple[nema_models.Strain, ...]:
        # First we can get all the strain numbers:
        all_strain_numbers = []
        for strain_range in self.strain_ranges.all():
            all_strain_numbers += list(range(strain_range.strain_numbers_start, strain_range.strain_numbers_end + 1))
        # Then we can use those strain numbers to return all the associated strains:
        return nema_models.Strain.objects.filter(wja__in=all_strain_numbers)


class StrainRange(models.Model):
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='strain_ranges')
    strain_numbers_start = models.IntegerField(default=-1)
    strain_numbers_end = models.IntegerField(default=-1)

    def clean(self):
        # Skip overlap check if both values are -1
        if self.strain_numbers_start == -1 and self.strain_numbers_end == -1:
            return
        # Check for overlapping ranges
        overlapping_ranges = StrainRange.objects.filter(
            user_profile=self.user_profile,
            strain_numbers_start__lte=self.strain_numbers_end,
            strain_numbers_end__gte=self.strain_numbers_start
        ).exclude(pk=self.pk)

        if overlapping_ranges.exists():
            raise ValidationError("Strain ranges cannot overlap with each other.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Validate model before saving
        super().save(*args, **kwargs)

    def __repr__(self):
        return f'Strain Range for {self.user_profile} ({self.strain_numbers_start}-{self.strain_numbers_end})'

    def __str__(self):
        return self.__repr__()
