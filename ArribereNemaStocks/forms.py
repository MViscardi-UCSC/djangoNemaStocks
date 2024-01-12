from django import forms
from .models import Strain, ThawRequest, FreezeRequest
from hardcoded import CAP_COLOR_OPTIONS

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
    
    request_comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Request Comments',
        help_text='Please enter any comments you have about this request. '
                  'These will only be visible to the strain czar during the thaw process.',
    )

class FreezeRequestForm(forms.ModelForm):
    
    class Meta:
        model = FreezeRequest
        fields = ['strain', 'requester', 'number_of_tubes', 'cap_color', 'request_comments',]
        
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
    
    request_comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Request Comments',
        help_text='Please enter any comments you have about this request. '
                  'These will only be visible to the strain czar during the freeze process.',
    )
    
    number_of_tubes = forms.IntegerField(
        label='Number of Tubes',
        help_text='Please enter the number of tubes to be frozen. Note: One tube will be used for thaw testing.',
    )
    
    cap_color = forms.ChoiceField(
        choices=CAP_COLOR_OPTIONS,
        label='Cap Color',
        help_text='Please select the cap color for the tubes.',
    )
