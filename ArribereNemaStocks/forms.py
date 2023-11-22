from django import forms
from .models import Strain

class StrainForm(forms.ModelForm):
    class Meta:
        model = Strain
        fields = ['wja', 'description']

class StrainEditForm(forms.ModelForm):
    class Meta:
        model = Strain
        fields = ['wja', 'description']

class NewFreezeForm(forms.Form):
    wja = forms.CharField(max_length=100, required=True)
    description = forms.CharField(max_length=255, required=False)