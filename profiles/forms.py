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
    class Meta:
        model = UserProfile
        fields = ['role', 'initials', 'active_status']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'initials': forms.TextInput(attrs={'class': 'form-control'}),
            'active_status': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'role': 'Role',
            'initials': 'Initials',
            'active_status': 'Active Status',
        }
        help_texts = {
            'role': 'Pleas select your role from the dropdown menu.',
            'initials': 'Enter your initials. These will be used to identify you in the database.',
            'active_status': 'Check this box if you are an active member of the lab.',
        }
        error_messages = {
            'initials': {
                'max_length': "Please enter a maximum of 4 characters.",
            },
        }