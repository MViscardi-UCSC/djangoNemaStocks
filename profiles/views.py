from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from . import models
from . import forms
# Create your views here.

def login_page(request):
    form = forms.LoginForm()
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
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
                message = 'Login failed!'
                messages.error(request, message)
    return render(request, 'authentication/login.html', context={'form': form})

@login_required
def user_page(request):
    user_profile = request.user.userprofile
    user_permissions = sorted(request.user.get_all_permissions())
    user_groups = sorted(request.user.groups.all())
    if request.method == 'POST':
        if 'logout' in request.POST:
            logout(request)
            messages.success(request, 'You have been logged out.')
            return redirect('login_page')
        
    return render(request, 'authentication/user.html',
                  context={'user_profile': user_profile,
                           'user_permissions': user_permissions,
                           'user_groups': user_groups})


@login_required
def edit_user_profile(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        form = forms.UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'User profile updated successfully!')
            return redirect('user_page')
    else:
        form = forms.UserProfileForm(instance=user_profile,
                                     initial={'email': user_profile.user.email})
    
    return render(request, 'authentication/edit_user_profile.html',
                  context={'form': form, 'user_profile': user_profile})
