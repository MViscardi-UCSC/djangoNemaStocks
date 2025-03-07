from datetime import date

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect, reverse
from django.contrib import messages
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.forms import formset_factory, modelformset_factory, BaseModelFormSet

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from django_tables2 import RequestConfig

from . import models as nema_models
from . import forms as nema_forms
from . import tables as nema_tables
from .utils import parse_strain_data

import profiles.models as profile_models

# TODO: Implement a way to "bulk change" the fields in the ongoing freeze and thaw requests tables
# TODO: Add a review slide for the ongoing freeze and thaw request tables, when submitting
# TODO: Remove canceled thaw requests from the strain details pages


# General Navigation:
def index(request, *args, **kwargs):
    user_registration = profile_models.OpenRegistration.objects.first().is_open
    registration_string = 'open' if user_registration else 'closed'
    edit_permissions = nema_models.OpenStrainEditing.objects.first().edit_ability
    edit_permissions_string = 'closed'
    if edit_permissions == 'N':
        edit_permissions_string = 'closed'
    elif edit_permissions == 'O':
        edit_permissions_string = 'open for owned strains'
    elif edit_permissions == 'A':
        edit_permissions_string = 'open for all strains'
    return render(request, 'basic_navigation/index.html',
                  {'registration': registration_string,
                   'edit_permissions': edit_permissions_string})


def about(request, *args, **kwargs):
    return render(request, 'basic_navigation/about.html')


# Strain Navigation:
def strain_assignments(request, *args, **kwargs):
    user_profiles = profile_models.UserProfile.objects.all()
    active_user_profiles = [user_profile for user_profile in user_profiles if user_profile.active_status]
    inactive_user_profiles = [user_profile for user_profile in user_profiles if not user_profile.active_status]
    return render(request, 'strains/strain_assignments.html',
                  {'active_user_profiles': active_user_profiles,
                   'inactive_user_profiles': inactive_user_profiles})


def strain_search(request, *args, **kwargs):
    return render(request, 'strains/strain_search.html')


def strain_list_datatable(request, *args, **kwargs):
    search_type = request.GET.get('search_type', 'search')
    search_term = request.GET.get('q')
    user_id = request.GET.get('user_id')
    user_profile_initials = request.GET.get('user_profile_initials')
    
    if user_profile_initials:
        user_profile = profile_models.UserProfile.objects.get(initials=user_profile_initials)
        strains = user_profile.get_all_strains()
    elif user_id:
        user_profile = profile_models.UserProfile.objects.get(user__id=user_id)
        strains = user_profile.get_all_strains()
    elif search_term:
        if search_type and search_type == 'deep_search':
            strains = nema_models.Strain.objects.deep_search(search_term)
        else:
            strains = nema_models.Strain.objects.search(search_term)
    else:
        strains = nema_models.Strain.objects.all()
    
    # If there is only one result we can redirect to the details page! But we'll add a message first.
    if strains.count() == 1:
        messages.info(request, f'Only one result found for "{search_term}"! Redirected to its details page.')
        return redirect('strain_details', wja=strains.first().wja)
    
    table = nema_tables.StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strains/strain_list_datatable.html',
                  {'table': table, 'results_count': strains.count()})


def new_strain(request, *args, **kwargs):
    form = nema_forms.StrainForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Let's add some quick checks to make sure the new strain is unique and in the user's range
        if nema_models.Strain.objects.filter(wja=form.cleaned_data['wja']).exists():
            messages.warning(request, 'This strain already exists! Please check the WJA and try again.')
            return redirect('new_strain')
        if not request.user.userprofile.check_if_wja_int_in_any_ranges(form.cleaned_data['wja']):
            messages.warning(request, 'This strain is not in your range! This SHOULD BE okay...')
        else:
            messages.success(request, 'This strain is unique and in your range! Creating new strain...')
        form.save()
        messages.success(request, 'New strain created successfully!')
        return redirect('strain_details', wja=form.cleaned_data['wja'])
    return render(request, 'strains/new_strain.html', {'form': form})


# Things for Bulk Upload
def bulk_upload_strains(request):
    if request.method == 'POST':
        form = nema_forms.BulkStrainUploadForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['data']
            parsed_strains = parse_strain_data(data)
            if not parsed_strains:
                form.add_error('data', 'No valid data found.')
                return render(request, 'strains/bulk_upload_strains.html', {'form': form})
            request.session['parsed_strains'] = parsed_strains
            return redirect('bulk_confirm_strains')
    else:
        form = nema_forms.BulkStrainUploadForm()
    return render(request, 'strains/bulk_upload_strains.html', {'form': form})


@transaction.atomic
def bulk_confirm_strains(request):
    if request.method == 'POST':
        # Reconstruct the formset without specifying 'extra'
        StrainFormSet = modelformset_factory(
            nema_models.Strain, form=nema_forms.MiniStrainForm, formset=BaseModelFormSet
        )
        formset = StrainFormSet(request.POST, queryset=nema_models.Strain.objects.none())
        if formset.is_valid():
            formset.save()
            request.session.pop('parsed_strains', None)
            return redirect('strain_list_datatable')
    else:
        parsed_strains = request.session.get('parsed_strains')
        if not parsed_strains:
            return redirect('bulk_upload_strains')
        total_forms = len(parsed_strains)
        # Set 'extra' to the number of parsed strains
        StrainFormSet = modelformset_factory(
            nema_models.Strain,
            form=nema_forms.MiniStrainForm,
            formset=BaseModelFormSet,
            extra=total_forms
        )
        formset = StrainFormSet(
            queryset=nema_models.Strain.objects.none(),
            initial=parsed_strains
        )
    return render(request, 'strains/bulk_confirm_strains.html', {'formset': formset})
# End Bulk Upload


def edit_strain(request, wja, *args, **kwargs):
    strain = get_object_or_404(nema_models.Strain, wja=wja)
    user = request.user
    
    open_editing_status = nema_models.OpenStrainEditing.objects.first().edit_ability
    
    # Check if user has permission to edit strains (All users should be given this permission)
    if not user.has_perm('ArribereNemaStocks.change_strain'):
        messages.warning(request, 'You do not have permission to edit strains! Please contact an admin.')
        return redirect('strain_details', wja=wja)
    else:
        print("User change_strain permission check passed.")
    
    # Go through all the possible editing statuses:
    if open_editing_status == 'N':  # No strain editing currently allowed
        if not (user.is_superuser or user.is_staff):
            messages.warning(request, 'Strain editing is currently disabled! Please contact an admin.')
            return redirect('strain_details', wja=wja)
    elif open_editing_status == 'O':  # Owned strain editing only
        if not user.userprofile.check_if_strain_in_any_ranges(strain):
            if not (user.is_superuser or user.is_staff):
                messages.warning(request, 'This is not one of your strains! '
                                          'Currently only owned strains can be edited. '
                                          'Contact an admin if you need to edit this strain.')
                return redirect('strain_details', wja=wja)
            else:
                messages.warning(request, 'This is not one of your strains, but you are an admin/staff. '
                                          'Please be careful to not break other peoples things.')
    elif open_editing_status == 'A':  # All strain editing allowed
        if not user.userprofile.check_if_strain_in_any_ranges(strain):
            messages.warning(request, 'This is not one of your strains, '
                                      'but editing is currently available to all users. '
                                      'Please be careful to not break anything.')
        else:
            print("User strain_range check passed.")
    
    form = nema_forms.StrainEditForm(request.POST or None, instance=strain)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.info(request, f'Strain {strain.formatted_wja} updated.')
            return redirect('strain_details', wja=form.instance.wja)
    
    return render(request, 'strains/edit_strain.html', {'form': form, 'strain': strain})


def strain_details(request, wja, *args, **kwargs):
    strain = get_object_or_404(nema_models.Strain, wja=wja)

    active_freeze_groups = [freeze_group for freeze_group in strain.freeze_groups.all()
                            if freeze_group.active_tubes_count() > 0]
    tubes_table = nema_tables.MiniFreezeGroupTable(active_freeze_groups)
    RequestConfig(request, paginate={"per_page": 10}).configure(tubes_table)

    recent_thaw_requests = strain.thaw_requests.all().order_by('-date_created')[:3]
    thaws_table = nema_tables.MiniThawRequestTable(nema_models.ThawRequest.objects.filter(pk__in=recent_thaw_requests))
    RequestConfig(request, paginate={"per_page": 10}).configure(thaws_table)
    
    recent_thawed_tube = strain.tube_set.filter(thawed=True).order_by('-date_thawed').first()

    return render(request, 'strains/strain_details.html', {'strain': strain,
                                                           'tubes_table': tubes_table,
                                                           'tubes_table_count': len(active_freeze_groups),
                                                           'thaws_table': thaws_table,
                                                           'thaws_table_count': len(recent_thaw_requests),
                                                           'recent_thawed_tube': recent_thawed_tube})


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
    
    form = nema_forms.InitialThawRequestForm(request.POST or None,
                                             initial={'strain': formatted_wja,
                                                      'requester': request.user.userprofile},
                                             strain_locked=strain_locked)

    if form.is_valid():
        strain_from_form = form.cleaned_data['strain']
        strain = get_object_or_404(nema_models.Strain, formatted_wja=strain_from_form.formatted_wja)
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
            'strain': get_object_or_404(nema_models.Strain,
                                        formatted_wja=formatted_wja),
            'requester': get_object_or_404(profile_models.UserProfile,
                                           initials=request.POST.get('requester',
                                                                     None)),
            'is_urgent': request.POST.get('is_urgent', None),
            'request_comments': request.POST.get('request_comments', None),
        }
    if request.method == 'POST' and 'confirm' in request.POST:
        thaw_request = nema_models.ThawRequest.objects.create(**thaw_request_data)
        
        messages.success(request,
                         f'New thaw request created successfully! '
                         f'Target: {formatted_wja}; ID: {thaw_request.id:>05d}')
        
        # let's email czars when a request is made
        def send_email_to_czars():
            recipients_list = []
            cc_list = []
            strain_czars = profile_models.UserProfile.objects.filter(is_strain_czar=True)
            for czar in strain_czars:
                if czar.user.email and czar.active_status:
                    recipients_list.append(czar.user.email)
            thaw_requester = thaw_request.requester
            thaw_requester_name = thaw_requester.user.first_name.title()
            if thaw_requester.user.email and thaw_requester.active_status:
                cc_list.append(thaw_requester.user.email)
            context = {
                'thaw_request': thaw_request,
                'strain': thaw_request.strain,
                'requester': thaw_request.requester,
                'requester_name': thaw_requester_name,
                'is_urgent': thaw_request.is_urgent,
                'request_comments': thaw_request.request_comments,
            }
            if thaw_request.is_urgent == "True":
                subject = (f"New URGENT Thaw Request by {thaw_requester.initials}: "
                           f"{thaw_request.strain.formatted_wja} (ID#{thaw_request.id:0>6d})")
            else:
                subject = f"New Thaw Request"
            message = render_to_string('freezes_and_thaws/thaw_request_email.txt', context)
            email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, recipients_list, cc=cc_list)
            email.send()
        send_email_to_czars()

        return redirect('outstanding_thaw_requests')

    return render(request, 'freezes_and_thaws/thaw_request_confirmation.html',
                  {'thaw_request_data': thaw_request_data,
                   'form': form})


def outstanding_thaw_requests(request):
    thaw_requests = nema_models.ThawRequest.objects.filter(status__in=['R', 'O'])
    requesting_users = profile_models.UserProfile.objects.filter(thaw_requests__in=thaw_requests).distinct()
    requesting_users_initials = [user_profile.initials for user_profile in requesting_users]

    # Table using django-tables2
    table = nema_tables.ThawRequestTable(thaw_requests)
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
            selected_requests = nema_models.ThawRequest.objects.filter(pk__in=selected_requests_pks)
        elif act_targets in requesting_users_initials:
            selected_requests = nema_models.ThawRequest.objects.filter(requester__initials=act_targets)
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

    thaw_requests = nema_models.ThawRequest.objects.filter(pk__in=thaw_request_ids.split('&'))

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
    ongoing_thaws = nema_models.ThawRequest.objects.filter(status__in=['O'])

    AdvThawFormSet = modelformset_factory(nema_models.ThawRequest,
                                          form=nema_forms.AdvancingThawRequestForm,
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
    form = nema_forms.FreezeRequestForm(request.POST or None,
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
            'strain': get_object_or_404(nema_models.Strain,
                                        formatted_wja=formatted_wja),
            'requester': get_object_or_404(profile_models.UserProfile,
                                           initials=request.POST.get('requester',
                                                                     None)),
            'request_comments': request.POST.get('request_comments', None),
            'number_of_tubes': request.POST.get('number_of_tubes', None),
            'cap_color': request.POST.get('cap_color', None),
        }
    if request.method == 'POST' and 'confirm' in request.POST:
        freeze_request = nema_models.FreezeRequest.objects.create(**freeze_request_data)

        messages.success(request, f'New freeze request created successfully! '
                                  f'Target: {formatted_wja}; ID: {freeze_request.id:>05d}')

        return redirect('outstanding_freeze_requests')
    return render(request, 'freezes_and_thaws/freeze_request_confirmation.html',
                  {'freeze_request_data': freeze_request_data,
                   'form': form})


def outstanding_freeze_requests(request):
    freeze_requests = nema_models.FreezeRequest.objects.filter(status__in=['R', 'A'])
    requesting_users = profile_models.UserProfile.objects.filter(freeze_requests__in=freeze_requests).distinct()
    requesting_users_initials = [user_profile.initials for user_profile in requesting_users]

    # Table using django-tables2
    table = nema_tables.FreezeRequestTable(freeze_requests)
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
            selected_requests = nema_models.FreezeRequest.objects.filter(pk__in=selected_requests_pks)
        elif act_targets in requesting_users_initials:
            selected_requests = nema_models.FreezeRequest.objects.filter(requester__initials=act_targets)
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
                    messages.warning(request, mark_safe(f'You cannot cancel an request that has moved on to testing'
                                                        f'from this page! Please do so from the ongoing freezes page. '
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

    freeze_requests = nema_models.FreezeRequest.objects.filter(pk__in=freeze_request_ids.split('&'))

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
    ongoing_freeze_set = nema_models.FreezeRequest.objects.filter(status='A')

    AdvFreezeFormSet = modelformset_factory(
        nema_models.FreezeRequest,
        form=nema_forms.AdvancingFreezeRequestForm,
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
    else:  # GET request
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
            # if not form.instance.box1:
            #     form.initial['box1'] = DefaultBox.get_default_box_for_dewar(1)
            # if not form.instance.box2:
            #     form.initial['box2'] = DefaultBox.get_default_box_for_dewar(2)

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


# Test things:
@transaction.atomic
def func_tester_page(request):
    context = {}
    # Let's see if we can look at the histories of all strains
    # for history_step in nema_models.Strain.history.all():
    #     print(history_step)
    return render(request, 'pieces/func_tester_page.html',
                  {'context': context})


def scary_stuff(request):
    failed_freeze_strains = nema_models.Strain.objects.filter(freeze_groups__passed_test=False).distinct()
    strains_with_most_recent_failures = []
    for strain in failed_freeze_strains:
        most_recent_freeze = strain.freeze_groups.order_by('-date_created').first()
        if most_recent_freeze.passed_test:
            continue
        strains_with_most_recent_failures.append(most_recent_freeze.strain)
    print(f"Finished collecting strains with failed freeze groups, there are {len(strains_with_most_recent_failures)}.")
    
    strains_without_freezes = nema_models.Strain.objects.exclude(freeze_groups__isnull=False)
    print(f"Finished collecting strains without freeze groups, there are {len(strains_without_freezes)}.")
    return render(request, 'basic_navigation/scary_stuff.html',
                    {'strains_with_fails': strains_with_most_recent_failures,
                     'strains_without_freezes': strains_without_freezes})
    
    

