from django.db import models
from django.contrib.auth.models import User, Group
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User, Group, AbstractUser
from hardcoded import ROLE_CHOICES

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='userprofile')
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='o')
    initials = models.CharField(max_length=4, null=False, blank=False, unique=True)
    active_status = models.BooleanField(default=False)
    strain_numbers_start = models.IntegerField(default=-1)
    strain_numbers_end = models.IntegerField(default=-1)
    
    history = HistoricalRecords()
    
    def __repr__(self):
        return f'{self.user.username.title()} ({self.initials})'
    
    def __str__(self):
        return self.__repr__()
