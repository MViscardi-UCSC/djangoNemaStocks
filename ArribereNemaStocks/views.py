from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect, reverse
from django.contrib import messages
from django.http import HttpResponse
from django_tables2 import RequestConfig

from . import models as nema_models
from . import forms as nema_forms
from . import tables as nema_tables

from profiles.models import UserProfile

from .json_DB_parser import main as json_db_parser_main


# General Navigation:
def index(request, *args, **kwargs):
    strains = nema_models.Strain.objects.all()
    return render(request, 'basic_navigation/index.html')


def about(request, *args, **kwargs):
    return render(request, 'basic_navigation/about.html')


# Strain Navigation:
def strain_search(request, *args, **kwargs):
    strains = nema_models.Strain.objects.all()
    search_term = request.GET.get('q')

    if search_term:
        strains = nema_models.Strain.objects.search(search_term)

    table = nema_tables.StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strains/strain_search.html', {'table': table, 'results_count': strains.count()})


def strain_list_datatable(request, *args, **kwargs):
    strains = nema_models.Strain.objects.all()
    search_term = request.GET.get('q')

    if search_term:
        strains = nema_models.Strain.objects.search(search_term)

    table = nema_tables.StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strains/strain_list_datatable.html', {'table': table, 'results_count': strains.count()})


def new_strain(request, *args, **kwargs):
    form = nema_forms.StrainForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'New strain created successfully!')
        return redirect('strain_details', wja=form.instance.wja)
    return render(request, 'strains/new_strain.html', {'form': form})


def edit_strain(request, wja, *args, **kwargs):
    strain = get_object_or_404(nema_models.Strain, wja=wja)
    form = nema_forms.StrainEditForm(request.POST or None, instance=strain)
    if form.is_valid():
        form.save()
        messages.info(request, 'Strain updated.')
        return redirect('strain_details', wja=form.instance.wja)
    return render(request, 'strains/edit_strain.html', {'form': form, 'strain': strain})


def strain_details(request, wja, *args, **kwargs):
    strain = get_object_or_404(nema_models.Strain, wja=wja)

    active_freeze_groups = [freeze_group for freeze_group in strain.freezegroup_set.all()
                            if freeze_group.active_tubes_count() > 0]
    tubes_table = nema_tables.MiniFreezeGroupTable(active_freeze_groups)
    RequestConfig(request, paginate={"per_page": 10}).configure(tubes_table)

    recent_thaw_requests = strain.thaw_requests.all().order_by('-date_created')[:3]
    thaws_table = nema_tables.MiniThawRequestTable(nema_models.ThawRequest.objects.filter(pk__in=recent_thaw_requests))
    RequestConfig(request, paginate={"per_page": 10}).configure(thaws_table)

    return render(request, 'strains/strain_details.html', {'strain': strain,
                                                           'tubes_table': tubes_table,
                                                           'tubes_table_count': len(active_freeze_groups),
                                                           'thaws_table': thaws_table,
                                                           'thaws_table_count': len(recent_thaw_requests)})


# Request Thaws and Freezes:
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
        messages.success(request, 'Please confirm the below information is correct.')
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
            'requester': get_object_or_404(UserProfile,
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

def thaw_request_form(request, *args, **kwargs):
    if not request.user.has_perm('ArribereNemaStocks.add_thawrequest'):
        if request.user.is_authenticated:
            messages.warning(request, 'You do not have permission to create thaw requests! Please contact an admin.')
        else:
            messages.warning(request, 'You do not have permission to create thaw requests! Please log in.')
        return redirect('strain_details', wja=request.GET.get('formatted_wja', None).lstrip('WJA'))

    formatted_wja = request.GET.get('formatted_wja', None)
    strain_locked = bool(formatted_wja)
    form = nema_forms.ThawRequestForm(request.POST or None,
                                      initial={'strain': formatted_wja,
                                               'requester': request.user.userprofile},
                                      strain_locked=strain_locked)
    
    if form.is_valid():
        # Redirect to the confirmation step
        return thaw_request_confirmation(request, form=form)

    return render(request, 'freezes_and_thaws/thaw_request_form.html', {'form': form})


# New thaw_request_confirmation view
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
            'requester': get_object_or_404(UserProfile,
                                           initials=request.POST.get('requester',
                                                                     None)),
            'is_urgent': request.POST.get('is_urgent', None),
            'request_comments': request.POST.get('request_comments', None),
        }
    if request.method == 'POST' and 'confirm' in request.POST:
        thaw_request = nema_models.ThawRequest.objects.create(**thaw_request_data)

        messages.success(request, f'New thaw request created successfully! Target: {formatted_wja}; ID: {thaw_request.id:>05d}')

        return redirect('outstanding_thaw_requests')

    return render(request, 'freezes_and_thaws/thaw_request_confirmation.html',
                  {'thaw_request_data': thaw_request_data,
                   'form': form})


# Outstanding Requests Lists:
def outstanding_freeze_requests(request):
    freeze_requests = nema_models.FreezeRequest.objects.filter(completed=False)
    search_term = request.GET.get('q')

    if search_term:
        freeze_requests = freeze_requests.search(search_term)

    table = nema_tables.FreezeRequestTable(freeze_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'freezes_and_thaws/outstanding_freeze_requests.html',
                  {'table': table,
                   'results_count': freeze_requests.count()})


def outstanding_thaw_requests(request):
    thaw_requests = nema_models.ThawRequest.objects.filter(completed=False)
    search_term = request.GET.get('q')

    if search_term:
        thaw_requests = thaw_requests.search(search_term)

    table = nema_tables.ThawRequestTable(thaw_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'freezes_and_thaws/outstanding_thaw_requests.html', {'table': table,
                                                                                'results_count': thaw_requests.count()})


# Other items:
def load_data_from_json(request, *args, **kwargs):
    json_db_parser_main()
    return HttpResponse('Completed')
