from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Strain, Tube, Box, FreezeGroup
from .forms import StrainForm, StrainEditForm, NewFreezeForm
from django.http import HttpResponse

from .json_DB_parser import main as json_db_parser_main

def index(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'index.html')

def about(request, *args, **kwargs):
    return render(request, 'about.html')

def strain_list(request, *args, **kwargs):
    strains = Strain.objects.all()
    return render(request, 'strain_list.html', {'strains': strains})

def tube_list(request, *args, **kwargs):
    tubes = Tube.objects.all()
    return render(request, 'tube_list.html', {'tubes': tubes})


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

# def load_data_from_json(request, *args, **kwargs):
#     json_db_parser_main()
#     return HttpResponse('Completed')
