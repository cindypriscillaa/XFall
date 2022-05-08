from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserForAdminPage

class CreateAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['full_name', 'email', 'username', 'password', 'password_confirmation', 'phone_number']

class LoginAdminForm(UserCreationForm):
    class Meta:
        model = UserForAdminPage
        fields = ['free', 'password'] 