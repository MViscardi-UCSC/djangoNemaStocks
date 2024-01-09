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
        fields = ['strain', 'requester', 'is_urgent', 'request_comments']
    
    def __init__(self, *args, **kwargs):
        strain_locked = kwargs.pop('strain_locked', False)
        super().__init__(*args, **kwargs)
        self.fields['strain'].widget.attrs['disabled'] = strain_locked

    strain = forms.ModelChoiceField(
        queryset=Strain.objects.all(),
        to_field_name='formatted_wja',
        widget=forms.TextInput(),
        label='Strain',
        help_text='Please enter the strain in this format: WJA0999',
    )

class FreezeRequestForm(forms.ModelForm):
    
    class Meta:
        model = FreezeRequest
        fields = ['strain', 'requester', 'request_comments', 'number_of_tubes', 'cap_color']
        
    def __init__(self, *args, **kwargs):
        strain_locked = kwargs.pop('strain_locked', False)
        super().__init__(*args, **kwargs)
        self.fields['strain'].widget.attrs['disabled'] = strain_locked

    strain = forms.ModelChoiceField(
        queryset=Strain.objects.all(),
        to_field_name='formatted_wja',
        widget=forms.TextInput(),
        label='Strain',
        help_text='Please enter the strain in this format: WJA0002',
    )
