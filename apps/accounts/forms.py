from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, EmployeeLevel

class EmployeeCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "level")

class LevelForm(forms.ModelForm):
    class Meta:
        model = EmployeeLevel
        fields = ("level", "name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
