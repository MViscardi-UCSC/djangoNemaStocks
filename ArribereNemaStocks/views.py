from datetime import date

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect, reverse
from django.contrib import messages
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.forms import formset_factory, modelformset_factory

from django_tables2 import RequestConfig

from .models import FreezeRequest, ThawRequest, Strain
from .forms import StrainEditForm, AdvancingFreezeRequestForm, StrainForm, InitialThawRequestForm, \
    AdvancingThawRequestForm, FreezeRequestForm
from .tables import StrainTable, MiniThawRequestTable, FreezeRequestTable, MiniFreezeGroupTable, ThawRequestTable

from profiles.models import UserProfile


# General Navigation:
def index(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'basic_navigation/index.html')


def about(request, *args, **kwargs):
    return render(request, 'basic_navigation/about.html')


def send_test_mail(request, *args, **kwargs):
    # TODO: Implement a email sending function
    pass


# Strain Navigation:
def strain_assignments(request, *args, **kwargs):
    user_profiles = UserProfile.objects.all()
    active_user_profiles = [user_profile for user_profile in user_profiles if user_profile.active_status]
    inactive_user_profiles = [user_profile for user_profile in user_profiles if not user_profile.active_status]
    return render(request, 'strains/strain_assignments.html',
                  {'active_user_profiles': active_user_profiles,
                   'inactive_user_profiles': inactive_user_profiles})


def strain_search(request, *args, **kwargs):
    return render(request, 'strains/strain_search.html')


def strain_list_datatable(request, *args, **kwargs):
    search_term = request.GET.get('q')
    user_id = request.GET.get('user_id')
    user_profile_initials = request.GET.get('user_profile_initials')
    
    if user_profile_initials:
        user_profile = UserProfile.objects.get(initials=user_profile_initials)
        strains = user_profile.get_all_strains()
    elif user_id:
        user_profile = UserProfile.objects.get(user__id=user_id)
        strains = user_profile.get_all_strains()
    elif search_term:
        strains = Strain.objects.search(search_term)
    else:
        strains = Strain.objects.all()

    table = StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strains/strain_list_datatable.html', {'table': table, 'results_count': strains.count()})


def new_strain(request, *args, **kwargs):
    # TODO: Get NEW STRAIN page working, with permission checks
    #       Additional checks for the new strain being unique and in the user's range
    form = StrainForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'New strain created successfully!')
        return redirect('strain_details', wja=form.instance.wja)
    return render(request, 'strains/new_strain.html', {'form': form})


def edit_strain(request, wja, *args, **kwargs):
    strain = get_object_or_404(Strain, wja=wja)
    user = request.user
    
    # Check if user has permission to edit strains
    if not user.has_perm('ArribereNemaStocks.change_strain'):
        messages.warning(request, 'You do not have permission to edit strains! Please contact an admin.')
        return redirect('strain_details', wja=wja)
    else:
        print("User change_strain permission check passed.")
    
    # Check if the strain is in the user's strain range
    # TODO: We could expand permissions to allow editing of strains that are not in the user's range.
    #       So super users can edit anything while regular users can only edit their own strains.
    if not user.userprofile.check_if_strain_in_any_ranges(strain):
        messages.warning(request, 'This is not one of your strains! Please be careful to not break anything. '
                                  '(Note to Marcus: This could be a security issue.)')
    else:
        print("User strain_range check passed.")
    
    form = StrainEditForm(request.POST or None, instance=strain)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.info(request, f'Strain {strain.formatted_wja} updated.')
            return redirect('strain_details', wja=form.instance.wja)
    
    return render(request, 'strains/edit_strain.html', {'form': form, 'strain': strain})


def strain_details(request, wja, *args, **kwargs):
    strain = get_object_or_404(Strain, wja=wja)

    active_freeze_groups = [freeze_group for freeze_group in strain.freezegroup_set.all()
                            if freeze_group.active_tubes_count() > 0]
    tubes_table = MiniFreezeGroupTable(active_freeze_groups)
    RequestConfig(request, paginate={"per_page": 10}).configure(tubes_table)

    recent_thaw_requests = strain.thaw_requests.all().order_by('-date_created')[:3]
    thaws_table = MiniThawRequestTable(ThawRequest.objects.filter(pk__in=recent_thaw_requests))
    RequestConfig(request, paginate={"per_page": 10}).configure(thaws_table)

    return render(request, 'strains/strain_details.html', {'strain': strain,
                                                           'tubes_table': tubes_table,
                                                           'tubes_table_count': len(active_freeze_groups),
                                                           'thaws_table': thaws_table,
                                                           'thaws_table_count': len(recent_thaw_requests)})


# Thaw Functionality:
def thaw_request_form(request, *args, **kwargs):
    if not request.user.has_perm('ArribereNemaStocks.add_thawrequest'):
        if request.user.is_authenticated:
            messages.warning(request, 'You do not have permission to create thaw requests! '
                                      'Please contact an admin.')
        else:
            messages.warning(request, 'You do not have permission to create thaw requests! Please log in.')
        return redirect('strain_details', wja=request.GET.get('formatted_wja', None).lstrip('WJA'))

    formatted_wja = request.GET.get('formatted_wja', None)
    strain_locked = bool(formatted_wja)
    
    form = InitialThawRequestForm(request.POST or None,
                                  initial={'strain': formatted_wja,
                                                      'requester': request.user.userprofile},
                                  strain_locked=strain_locked)

    if form.is_valid():
        strain_from_form = form.cleaned_data['strain']
        strain = get_object_or_404(Strain, formatted_wja=strain_from_form.formatted_wja)
        if strain.tube_set.filter(thawed=False).count() == 0:
            messages.warning(request, 'This strain has no tubes available to be thawed!')
            return redirect('strain_details', wja=strain_from_form.wja)
        # Redirect to the confirmation step
        return thaw_request_confirmation(request, form=form)

    return render(request, 'freezes_and_thaws/thaw_request_form.html', {'form': form})


def thaw_request_confirmation(request, form=None, *args, **kwargs):
    if form:
        formatted_wja = form.cleaned_data['strain'].formatted_wja
        thaw_request_data = {
            'strain': formatted_wja,
            'requester': form.cleaned_data['requester'].initials,
            'is_urgent': form.cleaned_data['is_urgent'],
            'request_comments': form.cleaned_data['request_comments'],
        }
    else:
        formatted_wja = request.POST.get('strain__formatted_wja', None)
        thaw_request_data = {
            'strain': get_object_or_404(Strain,
                                        formatted_wja=formatted_wja),
            'requester': get_object_or_404(UserProfile,
                                           initials=request.POST.get('requester',
                                                                     None)),
            'is_urgent': request.POST.get('is_urgent', None),
            'request_comments': request.POST.get('request_comments', None),
        }
    if request.method == 'POST' and 'confirm' in request.POST:
        thaw_request = ThawRequest.objects.create(**thaw_request_data)

        messages.success(request,
                         f'New thaw request created successfully! Target: {formatted_wja}; ID: {thaw_request.id:>05d}')

        return redirect('outstanding_thaw_requests')

    return render(request, 'freezes_and_thaws/thaw_request_confirmation.html',
                  {'thaw_request_data': thaw_request_data,
                   'form': form})


def outstanding_thaw_requests(request):
    thaw_requests = ThawRequest.objects.filter(status__in=['R', 'O'])
    requesting_users = UserProfile.objects.filter(thaw_requests__in=thaw_requests).distinct()
    requesting_users_initials = [user_profile.initials for user_profile in requesting_users]

    # Table using django-tables2
    table = ThawRequestTable(thaw_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    if request.method == 'POST':
        _, option, act_targets = next(k for k in request.POST if k.startswith('action')).split('-')
        selected_requests_pks = [pk for pk in request.POST.getlist('selected') if pk]
        if not selected_requests_pks and act_targets == 'selected':
            messages.warning(request, 'No thaw requests selected!')
            return redirect('outstanding_thaw_requests')
        if act_targets == "all":
            selected_requests = thaw_requests
        elif act_targets == "selected":
            selected_requests = ThawRequest.objects.filter(pk__in=selected_requests_pks)
        elif act_targets in requesting_users_initials:
            selected_requests = ThawRequest.objects.filter(requester__initials=act_targets)
        else:
            messages.warning(request, f'Invalid action target! You provided {act_targets}.')
            return redirect('outstanding_thaw_requests')

        if option == 'cancel' and not request.user.is_staff:
            for thaw_request in selected_requests:
                if thaw_request.requester != request.user.userprofile:
                    messages.warning(request, mark_safe(f'You do not have permission to cancel requests from '
                                                        f'other users! Removed the following from your request:'
                                                        f'<br><strong>{thaw_request}</strong>'))
            # Let's just remove the ones that are not from the current user
            selected_requests = selected_requests.filter(requester=request.user.userprofile)

        if not selected_requests:
            messages.warning(request, 'No thaw requests to process!')
            return redirect('outstanding_thaw_requests')

        selected_reqeust_ids_str = '&'.join([f"{request.id:>05d}" for request in selected_requests])

        # Redirect to the new page with selected ThawRequests
        return redirect('thaw_request_change_confirmation',
                        action=option,
                        thaw_request_ids=selected_reqeust_ids_str)

    return render(request, 'freezes_and_thaws/outstanding_thaw_requests.html',
                  {'table': table, 'requesting_users': requesting_users})


def thaw_request_change_confirmation(request, thaw_request_ids, action='NoAction', *args, **kwargs):
    if action not in ['cancel', 'advance']:
        messages.warning(request, f'Invalid action! You provided {action}.')
        return redirect('outstanding_thaw_requests')

    thaw_requests = ThawRequest.objects.filter(pk__in=thaw_request_ids.split('&'))

    if request.method == 'POST':
        if action == 'cancel':
            for thaw_request in thaw_requests:
                thaw_request.completed = True
                thaw_request.status = 'X'
                thaw_request.save()
                thaw_str = thaw_request.__str__()
                thaw_request.delete()
                messages.success(request, mark_safe(f'Deleted thaw request:<br><strong>{thaw_str}</strong>'))
            return redirect('outstanding_thaw_requests')
        elif action == 'advance':
            for thaw_request in thaw_requests:
                thaw_request.status = 'O'
                thaw_request.save()
                messages.success(request, f'Thaw requests {thaw_request_ids} advanced successfully!')
            return redirect('ongoing_thaws')
        else:
            messages.warning(request, f'Invalid action! You provided {action}.')
            return redirect('outstanding_thaw_requests')

    return render(request, 'freezes_and_thaws/thaw_request_change_confirmation.html',
                  {'thaw_request_ids': thaw_request_ids,
                   'thaw_requests': thaw_requests,
                   'action': action})


def ongoing_thaws(request):
    ongoing_thaws = ThawRequest.objects.filter(status__in=['O'])

    AdvThawFormSet = modelformset_factory(ThawRequest,
                                          form=AdvancingThawRequestForm,
                                          extra=0)
    
    if request.method == 'POST':
        adv_thaw_formset = AdvThawFormSet(request.POST, queryset=ongoing_thaws)
        # print(adv_thaw_formset)
        if adv_thaw_formset.is_valid():
            for form in adv_thaw_formset:
                messages.success(request, mark_safe(f'Saved changes to<br><strong>{form.instance}</strong>'))
                form.save()
            return redirect('ongoing_thaws')
        else:
            messages.warning(request, f'Invalid formset!{adv_thaw_formset.errors}')
    else:
        adv_thaw_formset = AdvThawFormSet(queryset=ongoing_thaws)
        for form in adv_thaw_formset:
            form.initial['thawed_by'] = request.user.userprofile
            form.initial['date_completed'] = date.today()

    return render(request, 'freezes_and_thaws/ongoing_thaws.html',
                  {'ongoing_thaws': ongoing_thaws,
                   'formset': adv_thaw_formset})


# Freeze Functionality:
def freeze_request_form(request, *args, **kwargs):
    if not request.user.has_perm('ArribereNemaStocks.add_freezerequest'):
        if request.user.is_authenticated:
            messages.warning(request, 'You do not have permission to create freeze requests! Please contact an admin.')
        else:
            messages.warning(request, 'You do not have permission to create freeze requests! Please log in.')
        return redirect('strain_details', wja=request.GET.get('formatted_wja', None).lstrip('WJA'))
    formatted_wja = request.GET.get('formatted_wja', None)
    number_of_tubes = request.GET.get('number_of_tubes', 1)
    strain_locked = bool(formatted_wja)
    form = FreezeRequestForm(request.POST or None,
                             initial={'strain': formatted_wja,
                                                 'number_of_tubes': number_of_tubes,
                                                 'requester': request.user.userprofile},
                             strain_locked=strain_locked)
    if form.is_valid():
        # Redirect to the confirmation step
        messages.info(request, 'Please confirm the below information is correct.')
        return freeze_request_confirmation(request, form=form)

    return render(request, 'freezes_and_thaws/freeze_request_form.html', {'form': form})


def freeze_request_confirmation(request, form=None, *args, **kwargs):
    if form:
        formatted_wja = form.cleaned_data['strain'].formatted_wja
        freeze_request_data = {
            'strain': formatted_wja,
            'requester': form.cleaned_data['requester'].initials,
            'request_comments': form.cleaned_data['request_comments'],
            'number_of_tubes': form.cleaned_data['number_of_tubes'],
            'cap_color': form.cleaned_data['cap_color'],
        }
    else:
        formatted_wja = request.POST.get('strain__formatted_wja', None)
        freeze_request_data = {
            'strain': get_object_or_404(Strain,
                                        formatted_wja=formatted_wja),
            'requester': get_object_or_404(UserProfile,
                                           initials=request.POST.get('requester',
                                                                     None)),
            'request_comments': request.POST.get('request_comments', None),
            'number_of_tubes': request.POST.get('number_of_tubes', None),
            'cap_color': request.POST.get('cap_color', None),
        }
    if request.method == 'POST' and 'confirm' in request.POST:
        freeze_request = FreezeRequest.objects.create(**freeze_request_data)

        messages.success(request, f'New freeze request created successfully! '
                                  f'Target: {formatted_wja}; ID: {freeze_request.id:>05d}')

        return redirect('outstanding_freeze_requests')
    return render(request, 'freezes_and_thaws/freeze_request_confirmation.html',
                  {'freeze_request_data': freeze_request_data,
                   'form': form})


def outstanding_freeze_requests(request):
    freeze_requests = FreezeRequest.objects.filter(status__in=['R', 'A'])
    requesting_users = UserProfile.objects.filter(freeze_requests__in=freeze_requests).distinct()
    requesting_users_initials = [user_profile.initials for user_profile in requesting_users]

    # Table using django-tables2
    table = FreezeRequestTable(freeze_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    # All the options include:
    # cancel-selected, cancel-all, cancel-<user initials>
    # advance-selected, advance-all, advance-<user initials>

    if request.method == 'POST':
        _, option, act_targets = next(k for k in request.POST if k.startswith('action')).split('-')
        selected_requests_pks = [pk for pk in request.POST.getlist('selected') if pk]
        if not selected_requests_pks and act_targets == 'selected':
            messages.warning(request, 'No freeze requests selected!')
            return redirect('outstanding_freeze_requests')
        if act_targets == "all":
            selected_requests = freeze_requests
        elif act_targets == "selected":
            selected_requests = FreezeRequest.objects.filter(pk__in=selected_requests_pks)
        elif act_targets in requesting_users_initials:
            selected_requests = FreezeRequest.objects.filter(requester__initials=act_targets)
        else:
            messages.warning(request, f'Invalid action target! You provided {act_targets}.')
            return redirect('outstanding_freeze_requests')

        if option == 'cancel' and not request.user.is_staff:
            for freeze_request in selected_requests:
                if freeze_request.requester != request.user.userprofile:
                    messages.warning(request, mark_safe(f'You do not have permission to cancel requests from '
                                                        f'other users! Removed the following from your request:'
                                                        f'<br><strong>{freeze_request}</strong>'))
                if freeze_request.status == 'A':
                    messages.warning(request, mark_safe(f'You cannot cancel an request that has moved on to testing! '
                                                        f'Removed the following from your request:'
                                                        f'<br><strong>{freeze_request}</strong>'))
                    # First lets just remove the ones that are not from the current user
            selected_requests = selected_requests.filter(requester=request.user.userprofile)
            selected_requests = selected_requests.exclude(status='A')

        if not selected_requests:
            messages.warning(request, 'No freeze requests to process!')
            return redirect('outstanding_freeze_requests')

        selected_reqeust_ids_str = '&'.join([f"{request.id:>05d}" for request in selected_requests])

        # Redirect to the new page with selected FreezeRequests
        return redirect('freeze_request_change_confirmation',
                        action=option,
                        freeze_request_ids=selected_reqeust_ids_str)

    return render(request, 'freezes_and_thaws/outstanding_freeze_requests.html',
                  {'table': table, 'requesting_users': requesting_users})


def freeze_request_change_confirmation(request, freeze_request_ids, action='NoAction', *args, **kwargs):
    if action not in ['cancel', 'advance']:
        messages.warning(request, f'Invalid action! You provided {action}.')
        return redirect('outstanding_freeze_requests')

    freeze_requests = FreezeRequest.objects.filter(pk__in=freeze_request_ids.split('&'))

    if request.method == 'POST':
        if action == 'cancel':
            for freeze_request in freeze_requests:
                freeze_request.status = 'X'
                freeze_request.save()
                freeze_str = freeze_request.__str__()
                freeze_request.delete()
                messages.success(request, mark_safe(f'Deleted thaw request:<br><strong>{freeze_str}</strong>'))
            return redirect('outstanding_thaw_requests')
        if action == 'advance':
            for freeze_request in freeze_requests:
                freeze_request.status = 'A'
                freeze_request.save()
                messages.success(request, f'Freeze request {freeze_request} advanced successfully!')
            return redirect('ongoing_freezes')
        else:
            messages.warning(request, f'Invalid action! You provided {action}.')
            return redirect('outstanding_freeze_requests')

    return render(request, 'freezes_and_thaws/freeze_request_change_confirmation.html',
                  {'freeze_request_ids': freeze_request_ids,
                   'freeze_requests': freeze_requests,
                   'action': action})


def ongoing_freezes(request):
    ongoing_freeze_set = FreezeRequest.objects.filter(status='A')

    AdvFreezeFormSet = modelformset_factory(
        FreezeRequest,
        form=AdvancingFreezeRequestForm,
        extra=0
    )

    if request.method == 'POST':
        formset = AdvFreezeFormSet(request.POST, queryset=ongoing_freeze_set)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Successfully updated freeze requests.")
            return redirect('ongoing_freezes')
        else:
            for form in formset:
                if form.errors:
                    messages.warning(request, mark_safe(f"Errors for request "
                                                        f"#{form.instance.id:0>6}:<br>{form.errors}"))
    else:
        formset = AdvFreezeFormSet(queryset=ongoing_freeze_set)

        for form in formset:
            # Set initial 'tester' to current user if not already set
            if not form.instance.tester:
                form.initial['tester'] = request.user.userprofile
            # Set initial 'freezer' to requester if not already set
            if not form.instance.freezer:
                form.initial['freezer'] = form.instance.requester

            # Set other initial data if necessary
            if not form.initial.get('tester_comments'):
                form.initial['tester_comments'] = ''
            if not form.initial.get('date_stored'):
                form.initial['date_stored'] = date.today()

            # Set initial tubes if not already set
            if form.instance.number_of_tubes and not (form.instance.tubes_for_box1 or form.instance.tubes_for_box2):
                if form.instance.id % 2 == 0:
                    form.initial['tubes_for_box1'] = form.instance.number_of_tubes - 2
                    form.initial['tubes_for_box2'] = 1
                else:
                    form.initial['tubes_for_box1'] = 1
                    form.initial['tubes_for_box2'] = form.instance.number_of_tubes - 2

    return render(request, 'freezes_and_thaws/ongoing_freezes.html', {
        'formset': formset,
        'ongoing_freezes': ongoing_freeze_set,
    })

