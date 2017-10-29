# Django
from django import forms

# Django Local
from prescription.validators import PrescriptionValidator


class CreatePrescriptionExamForm(forms.Form):
    """
    Form to create prescription.
    """
    patient = forms.CharField(widget=forms.TextInput(attrs={'class': 'transparent-input form-control patient-field',
                                                            'placeholder': 'Nome do Paciente:'}), required=False)

    cid = forms.CharField(widget=forms.TextInput(attrs={'class': 'transparent-input form-control',
                                                        'placeholder': 'CID'}), required=False)

    cid_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    validator = PrescriptionValidator()

    def clean(self):
        """
        Get prescription fields.
        """
        patient = self.cleaned_data.get('patient')
        cid = self.cleaned_data.get('cid')

        self.validator_all(patient, cid)

    def validator_all(self, patient, cid):
        self.validator.validator_cid(cid)
        self.validator.validator_pacient(patient)
