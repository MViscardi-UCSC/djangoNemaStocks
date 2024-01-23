"""
forms.py
Marcus Viscardi,    January 08, 2024


"""
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import UserProfile
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField()
<<<<<<< HEAD
    ROLE_CHOICES = UserProfile.ROLE_CHOICES
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'initials', 'active_status', 'email']

=======
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'initials', 'active_status', 'email', 'first_name', 'last_name']
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
>>>>>>> Another Flush, also adding better user side things
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['active_status'].help_text = 'This will control whether or not you receive emails.'
        
    def save(self, commit=True):
        user_profile = super(UserProfileForm, self).save(commit=False)
        user_profile.user.email = self.cleaned_data['email']
        user_profile.user.first_name = self.cleaned_data['first_name']
        user_profile.user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user_profile.user.save()
            user_profile.save()
        
        return user_profile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=UserProfileForm.ROLE_CHOICES, widget=forms.RadioSelect)
    initials = forms.CharField(max_length=3)
    active_status = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['active_status'].help_text = 'This will control whether or not you receive emails.'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name',
                  'role', 'initials', 'active_status')
        
    def clean_initials(self):
        initials = self.cleaned_data.get('initials')
        if UserProfile.objects.filter(initials=initials).exists():
            raise ValidationError("A user with these initials already exists.")
        return initials
    
    def save(self, commit=True):
        with transaction.atomic():
            user = super(RegistrationForm, self).save(commit=False)
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
                profile = UserProfile.objects.create(
                    user=user,
                    role=self.cleaned_data['role'],
                    initials=self.cleaned_data['initials'],
                    active_status=self.cleaned_data['active_status']
                )
            return user

