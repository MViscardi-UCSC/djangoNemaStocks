from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from . import models as profile_models
from . import forms as profile_forms
# Create your views here.


def register(request):
    status = profile_models.OpenRegistration.objects.first()
    if not status or not status.is_open:
        return render(request, 'authentication/registration_closed.html')
    
    if request.method == 'POST':
        form = profile_forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login_page')  # replace with your login url
    else:
        form = profile_forms.RegistrationForm()
    return render(request, 'authentication/register.html',
                  {'form': form})


def login_page(request):
    form = profile_forms.LoginForm()
    if request.method == 'POST':
        form = profile_forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                message = f'Hello {user.username}! You have been logged in'
                messages.success(request, message)
                return redirect('user_page')
            else:
                message = 'Login failed! Potentially incorrect username or password. Ask admin for help.'
                messages.warning(request, message)
    return render(request, 'authentication/login.html', context={'form': form})


@login_required
def user_page(request):
    user_profile = request.user.userprofile
    user_permissions = sorted(request.user.get_all_permissions())
    
    user_groups = request.user.groups.all()
    all_user_strains = user_profile.get_all_strains()
    
    if request.method == 'POST':
        if 'logout' in request.POST:
            logout(request)
            messages.success(request, 'You have been logged out.')
            return redirect('login_page')
        
    return render(request, 'authentication/user.html',
                  context={'user_profile': user_profile,
                           'user_permissions': user_permissions,
                           'all_user_strains': all_user_strains,
                           'user_groups': user_groups})


@login_required
def edit_user_profile(request):
    user_profile = request.user.userprofile

    if request.method == 'POST':
        form = profile_forms.UserProfileForm(request.POST, instance=user_profile)
        
        if form.is_valid():
            form.save()

            messages.success(request, 'User profile updated successfully!')
            return redirect('user_page')
        else:
            messages.warning(request, f'User profile update failed!: {form.errors}')
    else:
        form = profile_forms.UserProfileForm(instance=user_profile,
                                             initial={'email': user_profile.user.email})

    return render(request, 'authentication/edit_user_profile.html',
                  context={'form': form,
                           'user_profile': user_profile})
