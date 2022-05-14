from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import EmergencyServices, UserForAdminPage

class CreateAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['full_name', 'email', 'username', 'password', 'password_confirmation', 'phone_number']

class LoginAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['free', 'password'] 

class ServiceForm(ModelForm):
    class Meta:
        model = EmergencyServices 
        fields = ['type', 'name', 'address', 'phone_number']
