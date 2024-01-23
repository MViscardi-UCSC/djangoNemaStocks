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
    ROLE_CHOICES = UserProfile.ROLE_CHOICES
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'initials', 'active_status', 'email']

    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['active_status'].help_text = 'This will control whether or not you receive emails.'
        
    def save(self, commit=True):
        user_profile = super(UserProfileForm, self).save(commit=False)
        user_profile.user.email = self.cleaned_data['email']
        if commit:
            user_profile.user.save()
            user_profile.save()
        
        return user_profile

