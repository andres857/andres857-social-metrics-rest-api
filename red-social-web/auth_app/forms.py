from django import forms
from allauth.account.forms import SignupForm
from .models import CustomUser

class CustomSignupForm(SignupForm):
    type_identification = forms.ChoiceField(
        choices=CustomUser.ID_CHOICES,
        required=True,
        label="Tipo de Identificación"
    )
    identification = forms.CharField(
        max_length=20,
        required=True,
        label="Número de Identificación"
    )

    first_name = forms.CharField(max_length=30, label='Nombre', required=True)
    last_name = forms.CharField(max_length=30, label='Apellido', required=True)
    phone = forms.CharField(max_length=15, label='Teléfono', required=False)

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.type_identification = self.cleaned_data['type_identification']
        user.identification = self.cleaned_data['identification']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.save()
        return user