from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect, reverse
from django.contrib import messages
from django.http import HttpResponse
from django_tables2 import RequestConfig

from .models import Strain, Tube, Box, FreezeGroup, FreezeRequest, ThawRequest
from .forms import StrainForm, StrainEditForm, ThawRequestForm, FreezeRequestForm
from .tables import StrainTable, TubeTable, FreezeGroupTable, FreezeRequestTable, ThawRequestTable

from profiles.models import UserProfile

from .json_DB_parser import main as json_db_parser_main


# General Navigation:
def index(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'index.html')


def about(request, *args, **kwargs):
    return render(request, 'about.html')


# Strain Navigation:
def strain_search(request, *args, **kwargs):
    strains = Strain.objects.all()
    search_term = request.GET.get('q')

    if search_term:
        strains = Strain.objects.search(search_term)

    table = StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strain_search.html', {'table': table, 'results_count': strains.count()})

def strain_list_datatable(request, *args, **kwargs):
    strains = Strain.objects.all()
    search_term = request.GET.get('q')

    if search_term:
        strains = Strain.objects.search(search_term)

    table = StrainTable(strains)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'strain_list_datatable.html', {'table': table, 'results_count': strains.count()})


def new_strain(request, *args, **kwargs):
    form = StrainForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'New strain created successfully!')
        return redirect('strain_details', wja=form.instance.wja)
    return render(request, 'new_strain.html', {'form': form})


def edit_strain(request, wja, *args, **kwargs):
    strain = get_object_or_404(Strain, wja=wja)
    form = StrainEditForm(request.POST or None, instance=strain)
    if form.is_valid():
        form.save()
        messages.info(request, 'Strain updated.')
        return redirect('strain_details', wja=form.instance.wja)
    return render(request, 'edit_strain.html', {'form': form, 'strain': strain})


def strain_details(request, wja, *args, **kwargs):
    strain = get_object_or_404(Strain, wja=wja)
    active_freeze_groups = [freeze_group for freeze_group in strain.freezegroup_set.all()
                            if freeze_group.active_tubes_count() > 0]
    table = FreezeGroupTable(active_freeze_groups)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(request, 'strain_details.html', {'strain': strain, 'table': table})


# Request Thaws and Freezes:
def freeze_request_form(request, *args, **kwargs):
    formatted_wja = request.GET.get('formatted_wja', None)
    number_of_tubes = request.GET.get('number_of_tubes', 1)
    strain_locked = bool(formatted_wja)
    form = FreezeRequestForm(request.POST or None,
                             initial={'strain': formatted_wja,
                                      'number_of_tubes': number_of_tubes},
                             strain_locked=strain_locked)
    if form.is_valid():
        form.save()
        messages.success(request, 'New freeze request created successfully!')
        return redirect('outstanding_freeze_requests')
    else:
        print(form.errors)
    
    return render(request, 'freeze_request_form.html', {'form': form})


def thaw_request_form(request, *args, **kwargs):
    formatted_wja = request.GET.get('formatted_wja', None)
    strain_locked = bool(formatted_wja)
    form = ThawRequestForm(request.POST or None,
                           initial={'strain': formatted_wja},
                           strain_locked=strain_locked)
    if form.is_valid():
        form.save()
        messages.success(request, 'New thaw request created successfully!')
        return redirect('outstanding_thaw_requests')
    return render(request, 'thaw_request_form.html', {'form': form})


# Outstanding Requests Lists:
def outstanding_freeze_requests(request):
    freeze_requests = FreezeRequest.objects.filter(completed=False)
    search_term = request.GET.get('q')

    if search_term:
        freeze_requests = freeze_requests.search(search_term)

    table = FreezeRequestTable(freeze_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    
    return render(request, 'outstanding_freeze_requests.html', {'table': table,
                                                                'results_count': freeze_requests.count()})

def outstanding_thaw_requests(request):
    thaw_requests = ThawRequest.objects.filter(completed=False)
    search_term = request.GET.get('q')

    if search_term:
        thaw_requests = thaw_requests.search(search_term)

    table = FreezeRequestTable(thaw_requests)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, 'outstanding_thaw_requests.html', {'table': table,
                                                                'results_count': thaw_requests.count()})

# Other items:
def load_data_from_json(request, *args, **kwargs):
    json_db_parser_main()
    return HttpResponse('Completed')
