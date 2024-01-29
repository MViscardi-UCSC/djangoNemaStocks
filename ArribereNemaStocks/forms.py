import datetime

from django import forms
import ArribereNemaStocks.models as nema_models
from hardcoded import CAP_COLOR_OPTIONS


class StrainForm(forms.ModelForm):
    class Meta:
        model = nema_models.Strain
        fields = ['wja', 'description']


class StrainEditForm(forms.ModelForm):
    class Meta:
        model = nema_models.Strain
        fields = ['wja', 'description']


class InitialThawRequestForm(forms.ModelForm):
    class Meta:
        model = nema_models.ThawRequest
        fields = ['strain', 'requester', 'is_urgent', 'request_comments']

    def __init__(self, *args, **kwargs):
        strain_locked = kwargs.pop('strain_locked', False)
        super().__init__(*args, **kwargs)
        self.fields['strain'].widget.attrs['disabled'] = strain_locked

    strain = forms.ModelChoiceField(
        queryset=nema_models.Strain.objects.all(),
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
        required=False,
    )

    is_urgent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input',
                                          'id': 'flexSwitchCheckChecked'}),
        label='Is this request urgent?',
        help_text='Please check this box if this request is urgent.',
        required=False,
    )


class AdvancingThawRequestForm(forms.ModelForm):
    date_completed = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today()
    )
    
    save_changes = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input',
                                            'id': 'flexSwitchCheckChecked'}),
        label='Save Changes',
        help_text='Please check this box to save your changes when you click Submit.',
        required=False,
    )
    
    class Meta:
        model = nema_models.ThawRequest
        fields = ['tube', 'date_completed',
                  'status', 'thawed_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tube'].queryset = nema_models.Tube.objects.filter(strain=self.instance.strain,
                                                                           thawed=False,)
    
    def save(self, commit=True):
        if self.cleaned_data['save_changes']:
            if self.cleaned_data['status'] == 'C':
                self.instance.tube.thawed = True
                self.instance.tube.date_thawed = self.cleaned_data['date_completed']
                self.instance.tube.thawed_by = self.cleaned_data['thawed_by']
                self.instance.tube.thaw_requester = None  # TODO: figure out how to access the thaw request here!!
                self.instance.tube.save()
        return super().save(commit=commit)
    # TODO: Implement all of this for Freeze requests!


class FreezeRequestForm(forms.ModelForm):
    class Meta:
        model = nema_models.FreezeRequest
        fields = ['strain', 'requester', 'number_of_tubes', 'cap_color', 'request_comments',]
        
    def __init__(self, *args, **kwargs):
        strain_locked = kwargs.pop('strain_locked', False)
        super().__init__(*args, **kwargs)
        self.fields['strain'].widget.attrs['disabled'] = strain_locked
        self.fields['number_of_tubes'].widget.attrs['min'] = 1
        self.fields['number_of_tubes'].widget.attrs['max'] = 10
        self.fields['cap_color'].empty_label = None
        self.fields['cap_color'].required = True

    strain = forms.ModelChoiceField(
        queryset=nema_models.Strain.objects.all(),
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
        required=False,
    )

    number_of_tubes = forms.IntegerField(
        label='Number of Tubes',
        help_text='Please enter the number of tubes to be frozen. Note: One tube will be used for thaw testing.',
    )

    cap_color = forms.ChoiceField(
        choices=CAP_COLOR_OPTIONS,
        label='Cap Color',
        help_text='Please select the cap color for the tubes.',
        error_messages={'required': 'Please select a cap color.',
                        'invalid_choice': 'Please select a cap color.',
                        'invalid': 'Please select a cap color.',
                        },
    )


class FreezeRequestManagementForm(forms.Form):
    freeze_is_advancing = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input',
                                          'id': 'flexSwitchCheckChecked'}),
        label='Is this freeze advancing?',
        help_text='Please check this box if this freeze is advancing.',
        required=False,
    )
    freeze_advancing_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Freeze Advancing Date',
        help_text='Please select the date this freeze will be advancing.',
        required=False,
        initial=datetime.date.today(),
    )


class FreezeGroupForm(forms.ModelForm):
    class Meta:
        model = nema_models.FreezeGroup
        fields = ['strain',
                  'freezer',
                  'tester',
                  'started_test',
                  'completed_test',
                  'passed_test',
                  'stored',
                  ]
