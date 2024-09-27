import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages

import ArribereNemaStocks.models as nema_models
import profiles.models as profile_models
from hardcoded import CAP_COLOR_OPTIONS


class StrainForm(forms.ModelForm):
    class Meta:
        model = nema_models.Strain
        fields = ['wja', 'description', 'genotype', 'phenotype', 'additional_comments']
        help_texts = {
            'wja': 'Please enter the strain in this format: WJA0002 or just the number. '
                   'Aim to only add strains in your strain ranges!',
            'description': 'Please enter a brief description of the strain.',
            'genotype': 'Please provide a genotype in format "gene1(allele1#)chr1; gene2(allele2#)chr2", '
                        'for example: skih-2(cc2854;PTC)IV; unc-54(cc2865)I',
            'phenotype': 'Please enter the phenotype of the strain, for example: "slow growth, pvl"',
            'additional_comments': 'Please enter any additional comments about the strain, '
                                   'such as how the strain was constructed.',
        }


class StrainEditForm(forms.ModelForm):
    class Meta:
        model = nema_models.Strain
        fields = ['description', 'genotype', 'phenotype', 'additional_comments']
        help_texts = {
            'description': 'Please enter a brief description of the strain.',
            'genotype': 'Please provide a genotype in format "gene1(allele1#)chr1; gene2(allele2#)chr2", '
                        'for example: skih-2(cc2854;PTC)IV; unc-54(cc2865)I',
            'phenotype': 'Please enter the phenotype of the strain, for example: "slow growth, pvl"',
            'additional_comments': 'Please enter any additional comments about the strain, '
                                   'such as how the strain was constructed.',
        }


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
    
    class Meta:
        model = nema_models.ThawRequest
        fields = ['tube',
                  'date_completed',
                  'status',
                  'thawed_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tube'].queryset = nema_models.Tube.objects.filter(strain=self.instance.strain,
                                                                           thawed=False,)
            self.fields['tube'].label_from_instance = self.tube_label_from_instance_with_comments
            
    @staticmethod
    def tube_label_from_instance_with_comments(tube):
        return (f"{tube.box.short_pos_repr()} - {tube.freeze_group.tester.initials} "
                f"({tube.date_created}): {tube.freeze_group.tester_comments}")
    
    def save(self, commit=True):
        if self.cleaned_data['status'] == 'C':
            self.instance.tube.thawed = True
            self.instance.tube.date_thawed = self.cleaned_data['date_completed']
            self.instance.tube.thawed_by = self.cleaned_data['thawed_by']
            self.instance.tube.thaw_requester = self.instance.requester
            self.instance.tube.save()
        return super().save(commit=commit)


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


class AdvancingFreezeRequestForm(forms.ModelForm):
    # Constants and field definitions
    FULL_BOX_WIGGLE_ROOM = 11  # 81 spaces per box, but we won't show boxes that are within this many tubes of full

    box1 = forms.ModelChoiceField(
        queryset=nema_models.Box.objects.annotate(
            active_tubes_count=Count('tube_set', filter=Q(tube_set__thawed=False))
        ).filter(active_tubes_count__lt=81 - FULL_BOX_WIGGLE_ROOM).filter(dewar__exact=1),
        label='Box 1',
        help_text='Please select the box number for the first box.',
        required=False,
    )
    tubes_for_box1 = forms.IntegerField(
        label='Tubes for Box 1',
        help_text='Please enter the number of tubes to be placed in the first box.',
        min_value=0,
        max_value=81 - FULL_BOX_WIGGLE_ROOM,
        required=False,
    )
    box2 = forms.ModelChoiceField(
        queryset=nema_models.Box.objects.annotate(
            active_tubes_count=Count('tube_set', filter=Q(tube_set__thawed=False))
        ).filter(active_tubes_count__lt=81 - FULL_BOX_WIGGLE_ROOM).filter(dewar__exact=2),
        label='Box 2',
        help_text='Please select the box number for the second box.',
        required=False,
    )
    tubes_for_box2 = forms.IntegerField(
        label='Tubes for Box 2',
        help_text='Please enter the number of tubes to be placed in the second box.',
        min_value=0,
        max_value=81 - FULL_BOX_WIGGLE_ROOM,
        required=False,
    )

    # Fields from FreezeGroup
    tester = forms.ModelChoiceField(
        queryset=profile_models.UserProfile.objects.all(), required=False)
    freezer = forms.ModelChoiceField(
        queryset=profile_models.UserProfile.objects.all(), required=False)
    tester_comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False)
    date_stored = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date(), required=False)

    class Meta:
        model = nema_models.FreezeRequest
        fields = [
            'id',
            'box1', 'tubes_for_box1',
            'box2', 'tubes_for_box2',
            'freezer',
            'tester',
            'status',
            'tester_comments',
            'date_stored',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        default_box1 = nema_models.DefaultBox.get_default_box_for_dewar(1)
        default_box2 = nema_models.DefaultBox.get_default_box_for_dewar(2)
        # print(self.fields['box1'].data, self.fields['box2'].data)
        if not self.is_bound:
            # Remove initial data setting for 'freezer' and 'tester'
            # Set initial data only if not already set
            if not self.fields['tester_comments'].initial:
                self.fields['tester_comments'].initial = ''
            if not self.fields['date_stored'].initial:
                self.fields['date_stored'].initial = datetime.date.today()
            # Set initial tubes if not already set
            if self.instance.number_of_tubes and not (self.instance.tubes_for_box1 or self.instance.tubes_for_box2):
                if self.instance.id % 2 == 0:
                    self.fields['tubes_for_box1'].initial = self.instance.number_of_tubes - 2
                    self.fields['tubes_for_box2'].initial = 1
                else:
                    self.fields['tubes_for_box1'].initial = 1
                    self.fields['tubes_for_box2'].initial = self.instance.number_of_tubes - 2
        print('avail to fix')
        # Handle bound form (POST request with potentially empty data)
        print(self.data.get('box1'), self.data.get('box2'))
        print(default_box1, default_box2)
        # TODO: Fix this so that it actually selects the default box!!!
        if not self.data.get('box1') and default_box1:
            print('setting box1')
            self.fields['box1'].value = default_box1.box
        if not self.data.get('box2') and default_box2:
            self.fields['box2'].value = default_box2.box.pk
        print(self.data.get('box1'), self.data.get('box2'))

    def clean(self):
        cleaned_data = super().clean()
        box1 = cleaned_data.get('box1', None)
        tubes_for_box1 = cleaned_data.get('tubes_for_box1', 0)
        box2 = cleaned_data.get('box2', None)
        tubes_for_box2 = cleaned_data.get('tubes_for_box2', 0)
        number_of_tubes_requested = self.instance.number_of_tubes

        total_tubes_stored = tubes_for_box1 + tubes_for_box2

        status = cleaned_data.get('status')
        tester_comments = cleaned_data.get('tester_comments')
        
        print(f"Cleaning #{self.instance.id}:\n"
              f"  Status: {status}\n"
              f"  Total Tubes Stored: {total_tubes_stored} ({tubes_for_box1} + {tubes_for_box2})\n"
              f"  Number of Tubes Requested: {number_of_tubes_requested}\n")
        if status in ['C', 'A']:
            if total_tubes_stored + 1 > number_of_tubes_requested:
                tube_total_error = (f'The total number of tubes stored ({total_tubes_stored}) '
                                    f'is more than the number of tubes requested '
                                    f'({number_of_tubes_requested} -1 for testing).')
                self.add_error('tubes_for_box1', tube_total_error)
                self.add_error('tubes_for_box2', tube_total_error)
            elif total_tubes_stored + 1 != number_of_tubes_requested:
                tube_total_warning = (f'The total number of tubes stored ({total_tubes_stored}) '
                                      f'is not equal to the number of tubes requested '
                                      f'({number_of_tubes_requested} -1 for testing).')
                self.warnings.append(tube_total_warning)
        if status == 'C':
            if not tester_comments:
                self.add_error('tester_comments', 'Please enter comments regarding the completed freeze.')
            if not box1 and tubes_for_box1 > 0:
                self.add_error('box1', 'Please select a "Box1".')
            if not box2 and tubes_for_box2 > 0:
                self.add_error('box2', 'Please select a "Box2".')
            if box1.get_active_tubes().count() + tubes_for_box1 > 81:
                self.add_error('tubes_for_box1', 'The selected box would be overfull if you added to it.')
            if box2.get_active_tubes().count() + tubes_for_box2 > 81:
                self.add_error('tubes_for_box2', 'The selected box would be overfull if you added to it.')
        elif status in ['F', 'X']:
            if not tester_comments:
                self.add_error('tester_comments', 'Please enter comments regarding '
                                                  'the failed or cancelled freeze.')
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            cleaned_data = self.cleaned_data
            status = cleaned_data.get('status')

            # Proceed only if the form is valid
            if self.errors:
                raise ValidationError('Please correct the errors below.')

            # Call super().save(commit=False) to get the form data into self.instance
            instance = super().save(commit=False)

            if status in ['C', 'F', 'X']:
                if not instance.freeze_group:
                    # Create FreezeGroup instance
                    freeze_group = nema_models.FreezeGroup.objects.create(
                        strain=instance.strain,
                        freezer=cleaned_data.get('freezer'),
                        tester=cleaned_data.get('tester'),
                        started_test=True if status in ['C', 'F'] else False,
                        completed_test=True if status in ['C', 'F'] else False,
                        passed_test=True if status == 'C' else False,
                        stored=True if status == 'C' else False,
                        tester_comments=cleaned_data.get('tester_comments'),
                        freeze_request=instance,
                        date_stored=cleaned_data.get('date_stored'),
                        test_check_date=cleaned_data.get('date_stored'),
                    )

                    # Create Tube instances if status is 'C' (Completed)
                    if status == 'C':
                        for box, tubes in [
                            (cleaned_data.get('box1'), cleaned_data.get('tubes_for_box1')),
                            (cleaned_data.get('box2'), cleaned_data.get('tubes_for_box2'))
                        ]:
                            if box and tubes:
                                for i in range(tubes):
                                    nema_models.Tube.objects.create(
                                        strain=instance.strain,
                                        freeze_group=freeze_group,
                                        date_created=cleaned_data.get('date_stored'),
                                        box=box,
                                        cap_color=instance.cap_color,
                                        set_number=i + 1,
                                    )
                                # Update the default box for the dewar if we are freezing into non-default boxes!
                                if not nema_models.DefaultBox.objects.filter(box=box).exists():
                                    nema_models.DefaultBox.get_default_box_for_dewar(box.dewar).delete()
                                    nema_models.DefaultBox.objects.create(box=box)
                    instance.freeze_group = freeze_group
                    instance.date_advanced = timezone.now().date()

            # Update any additional fields on the instance that are not handled by the form
            # For example, if you have fields that are not in the form but need to be updated

            if commit:
                instance.save()
            return instance
