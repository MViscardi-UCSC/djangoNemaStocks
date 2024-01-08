from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('i', 'Professor/Primary Investigator'),
        ('p', 'Postdoctoral Fellow'),
        ('c', 'Collaborator'),
        ('g', 'Graduate Student'),
        ('t', 'Technician'),
        ('u', 'Undergraduate'),
        ('o', 'Other/Undefined'),
    ]
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='o')
    initials = models.CharField(max_length=4, null=False, blank=False, unique=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    active_status = models.BooleanField(default=False)
    
    def __repr__(self):
        return f'{self.user.username.title()} ({self.initials})'
    
    def __str__(self):
        return self.__repr__()
