from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import EmergencyServices, ServiceTypes, UserForAdminPage

SERVICES_TYPES = [
    ('1', 'Rumah Sakit'),
    ('2', 'Puskesmas'),
    ('3', 'Klinik'),
]

class CreateAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['full_name', 'email', 'username', 'password', 'password_confirmation', 'phone_number']

class LoginAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['free', 'password'] 

class ServiceForm(ModelForm):
    type = forms.ChoiceField(choices=SERVICES_TYPES)
    class Meta:
        model = EmergencyServices 
        fields = ['type', 'name', 'address', 'phone_number']
