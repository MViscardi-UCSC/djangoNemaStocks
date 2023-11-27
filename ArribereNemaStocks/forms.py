from django import forms
from .models import Strain, Tube, Box, FreezeGroup, ThawRequest, FreezeRequest

class StrainForm(forms.ModelForm):
    class Meta:
        model = Strain
        fields = ['wja', 'description']

class StrainEditForm(forms.ModelForm):
    class Meta:
        model = Strain
        fields = ['wja', 'description']

class ThawRequestForm(forms.ModelForm):
    class Meta:
        model = ThawRequest
        exclude = ['tube', 'date_completed', 'completed', 'thawed_by']
