from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django_tables2 import RequestConfig

from .models import Strain, Tube, Box, FreezeGroup
from .forms import StrainForm, StrainEditForm, ThawRequestForm
from .tables import StrainTable, TubeTable


from .json_DB_parser import main as json_db_parser_main

# General Navigation:
def index(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'index.html')

def about(request, *args, **kwargs):
    return render(request, 'about.html')


def tube_list(request, *args, **kwargs):
    tubes = Tube.objects.all()
    return render(request, 'tube_list.html', {'tubes': tubes})

def tube_list_datatable(request, *args, **kwargs):
    tubes = Tube.objects.all()
    search_term = request.GET.get('q')
    if search_term:
        strains = tubes.filter(formatted_wja__icontains=search_term)
    table = TubeTable(tubes)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, 'tube_list_datatable.html', {'table': table})


# Strain Navigation:
def strain_list(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'strain_list.html', {'strains': strains})

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
    return render(request, 'strain_details.html', {'strain': strain})

# Request Thaws and Freezes:
def thaw_request_view(request, *args, **kwargs):
    form = ThawRequestForm(request.POST or None)
    
    if form.is_valid():
        thaw_request = form.save(commit=False)
        target_strain = get_object_or_404(Strain, wja=thaw_request.strain.wja)
        # Add code to get the target_tube from the target_strain!
        form.save()
        messages.success(request, 'Thaw request submitted successfully!')
        return redirect('strain_details', wja=target_strain.wja)
    return render(request, 'thaw_request.html', {'form': form})

# Other items:
def load_data_from_json(request, *args, **kwargs):
    json_db_parser_main()
    return HttpResponse('Completed')
