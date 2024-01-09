"""
forms.py
Marcus Viscardi,    January 08, 2024


"""
from django import forms
from .models import UserProfile
from django.contrib.auth.models import User, Group

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = UserProfile
        fields = ['role', 'initials', 'active_status',
                  'strain_numbers_start', 'strain_numbers_end', 'email']
    ROLE_CHOICES = [
        ('i', 'Professor/Primary Investigator'),
        ('p', 'Postdoctoral Fellow'),
        ('c', 'Collaborator'),
        ('g', 'Graduate Student'),
        ('t', 'Technician'),
        ('u', 'Undergraduate'),
        ('o', 'Other/Undefined'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        user_profile = super(UserProfileForm, self).save(commit=False)
        user_profile.user.email = self.cleaned_data['email']
        if commit:
            user_profile.user.save()
            user_profile.save()
        return user_profile

