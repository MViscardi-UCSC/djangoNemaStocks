from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import User, Group, AbstractUser

from simple_history.models import HistoricalRecords

from hardcoded import ROLE_CHOICES
import ArribereNemaStocks.models as nema_models

from typing import List, Tuple, Union

# Create your models here.
class OpenRegistration(models.Model):
    is_open = models.BooleanField(default=False)
    
    def __repr__(self):
        return f'Open Registration: {self.is_open}'
    
    def __str__(self):
        return self.__repr__()


class UserProfile(models.Model):
    ROLE_CHOICES = ROLE_CHOICES
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='userprofile')
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='o')
    initials = models.CharField(max_length=4, null=False, blank=False, unique=True)  # These are the primary ones used!
    active_status = models.BooleanField(default=False)
    is_strain_czar = models.BooleanField(default=False)
    
    simp_history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        UserInitials.objects.update_or_create(initials=self.initials, defaults={'user_profile': self})
    
    def add_initials(self, initials):
        UserInitials.objects.create(user_profile=self, initials=initials)
    
    def __repr__(self):
        return f'{self.initials} ({self.user.username.title()})'
    
    def __str__(self):
        return self.__repr__()
    
    def get_all_strains(self) -> Tuple[nema_models.Strain, ...]:
        # First we can get all the strain numbers:
        all_strain_numbers_lists = []
        for strain_range in self.strain_ranges.all():
            all_strain_numbers_lists.append(list(range(strain_range.strain_numbers_start,
                                                 strain_range.strain_numbers_end + 1)))
        # Then we can use those strain numbers to return all the associated strains:
        all_strain_numbers = [strain_number for strain_number_list in all_strain_numbers_lists
                              for strain_number in strain_number_list]
        return nema_models.Strain.objects.filter(wja__in=all_strain_numbers)
    
    def check_if_strain_in_any_ranges(self, strain: nema_models.Strain) -> bool:
        for strain_range in self.strain_ranges.all():
            if strain_range.check_if_strain_in_range(strain):
                return True
        return False
    
    def check_if_wja_int_in_any_ranges(self, wja_int: int) -> bool:
        for strain_range in self.strain_ranges.all():
            if strain_range.check_if_wja_int_in_range(wja_int):
                return True
        return False


class UserInitials(models.Model):
    initials = models.CharField(max_length=4, null=False, blank=False, unique=True)
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE,
                                     related_name='all_associated_initials',
                                     null=True)

    def __repr__(self):
        return self.initials

    def __str__(self):
        return self.__repr__()


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
        return f'({self.user_profile.initials} WJAs: {self.strain_numbers_start}-{self.strain_numbers_end})'

    def __str__(self):
        return self.__repr__()
    
    def get_strains(self) -> Tuple[nema_models.Strain, ...]:
        # First we can get all the strain numbers:
        all_strain_numbers = list(range(self.strain_numbers_start, self.strain_numbers_end + 1))
        # Then we can use those strain numbers to return all the associated strains:
        return nema_models.Strain.objects.filter(wja__in=all_strain_numbers)
    
    def check_if_strain_in_range(self, strain: nema_models.Strain) -> bool:
        return self.strain_numbers_start <= strain.wja <= self.strain_numbers_end
    
    def check_if_wja_int_in_range(self, wja_int: int) -> bool:
        return self.strain_numbers_start <= wja_int <= self.strain_numbers_end
    
    def get_usage_string(self) -> str:
        strains = self.get_strains()
        num_strains = len(strains)
        potential_num_strains = self.strain_numbers_end - self.strain_numbers_start+1
        return_str = (f"{num_strains} of {potential_num_strains} "
                      f"assigned WJA{'s' if potential_num_strains > 1 else ''} used")
        return return_str
    
    def get_short_summary(self, with_initials=False) -> str:
        summary_string = ""
        if with_initials:
            summary_string += f"{self.user_profile.initials} "
        summary_string += (f"WJA{self.strain_numbers_start:0>4} - "
                           f"WJA{self.strain_numbers_end:0>4} "
                           f"({self.get_usage_string()})")
        return summary_string
    
    def get_html_summer_with_link(self, with_initials=False) -> str:
        summary_string = ("This would be really nice to get working. The idea would be to have "
                          "it link to the strain datatables with the strain range pre-populated "
                          "in the search bar). In order to do this I would need to implement a "
                          "specific ability to query in a WJA range!!")
        raise NotImplementedError(summary_string)

